import pandas as pd

from .lookups import standard_column_names as CN


class Aggregation:
	KeepLongest = 7
	LengthWeightedAverage = 2
	LengthWeightedPercentile = 4


class InfillType:
	none = 1
	value = 2


class Infill:
	def __init__(self, strategy, value):
		"""don't initialise directly, use the static builder methods"""
		self.type: str = strategy
		self.value = value
	
	@staticmethod
	def value(value):
		return Infill(InfillType.value, value)
	
	@staticmethod
	def none():
		return Infill(InfillType.none, None)


class Action:
	def __init__(
			self,
			column_name: str,
			aggregation: Aggregation,
			percentile: float = 0,
			infill: Infill = Infill.none()
	):
		
		self.column_name: str = column_name
		self.aggregation: Aggregation = aggregation
		self.percentile: float = percentile
		self.infill: Infill = infill
		if percentile > 1.0 or percentile < 0:
			raise ValueError("Percentile out of range")
		if aggregation == Aggregation.LengthWeightedPercentile and percentile == 0:
			raise ValueError("Percentile argument must be greater than zero and less than 1.0 when using a Percentile Aggregation")


def on_slk_intervals(target: pd.DataFrame, data: pd.DataFrame, join_left: list[str], column_actions: list[Action]):
	# precalculate slk_length for each row of data
	# data.loc[:, CN.slk_length] = data[CN.slk_to] - data[CN.slk_from]
	
	# reindex data for faster lookup
	data['merge_index'] = data.index
	data = data.set_index([*join_left, 'merge_index'])
	data = data.sort_index()
	
	result_index = []
	result_rows = []
	
	# Group target data by Road Number and Carriageway, loop over groups
	try:
		target_groups = target.groupby(join_left)
	except Exception as e:
		print(f"failed to group by {join_left}")
		print(f"target had columns {target.columns}")
		for uniquelist, col in [(list(target.loc[:,col].unique()), col) for col in join_left if col in target.columns]:
			print(f"target column {col} had unique list {uniquelist}")
		raise e

	for group_index, target_group in target_groups:
		try:
			data_matching_target_group = data.loc[group_index, :]
		except KeyError:
			continue
		except TypeError:
			print(data)
			print(group_index)
			return
			pass
		
		for target_index, target_row in target_group.iterrows():
			data_to_aggregate_for_target_group = data_matching_target_group[
				(data_matching_target_group[CN.slk_from] < target_row[CN.slk_to]) &
				(data_matching_target_group[CN.slk_to] > target_row[CN.slk_from])
			].copy()
			
			# if no data matches the target group do the infill strategy
			if len(data_to_aggregate_for_target_group.index) == 0:
				aggregated_result = []
				for column_action_index, column_action in enumerate(column_actions):
					if column_action.infill.type == InfillType.none:
						aggregated_result.append(None)
					elif column_action.infill.type == InfillType.value:
						aggregated_result.append(column_action.infill.value)
					else:
						raise Exception("unknown infill type")
				result_rows.append(aggregated_result)
				result_index.append(target_index)
				continue
			
			# compute overlap metrics for each row of data
			overlap_min = data_to_aggregate_for_target_group[CN.slk_from].apply(max, args=[target_row[CN.slk_from]])
			overlap_max = data_to_aggregate_for_target_group[CN.slk_to].apply(min, args=[target_row[CN.slk_to]])
			overlap_len = overlap_max - overlap_min
			
			# the sum of the length of all data segments overlapping the target segment
			total_overlap_length = overlap_len.sum()
			
			# for each column of data that we keep, we must aggregate each field down to a single value
			aggregated_result = []
			for column_action_index, column_action in enumerate(column_actions):
				if column_action.aggregation == Aggregation.LengthWeightedAverage:
					aggregated_result.append(
						(data_to_aggregate_for_target_group[column_action.column_name] * overlap_len / total_overlap_length).sum()
					)
				
				elif column_action.aggregation == Aggregation.KeepLongest:
					aggregated_result.append(
						data_to_aggregate_for_target_group[column_action.column_name].loc[overlap_len.idxmax()]
					)
				
				elif column_action.aggregation == Aggregation.LengthWeightedPercentile:
					aggregated_result.append(
						(data_to_aggregate_for_target_group[column_action.column_name] * overlap_len / total_overlap_length).quantile(column_action.percentile)
					)
			result_index.append(target_index)
			result_rows.append(aggregated_result)
	
	return target.join(
		pd.DataFrame(
			result_rows,
			columns=[x.column_name for x in column_actions],
			index=result_index
		)
	)
