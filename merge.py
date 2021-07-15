import numpy.typing
import pandas as pd

from .lookups import standard_column_names as CN


class Aggregation:
	KeepLongest = 7
	LengthWeightedAverage = 2
	LengthWeightedPercentile = 4


class InfillType:
	none = 1
	value = 2
	average = 3
	last = 4


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
	
	# @staticmethod
	# def last():
	# 	return Infill(InfillType.last, None)


class Action:
	def __init__(
			self,
			column_name: str,
			aggregation: Aggregation,
			percentile: float = 0,
			dtype: numpy.typing.DTypeLike = "f8",
			infill: Infill = Infill.none()
	):
		
		self.column_name: str = column_name
		self.aggregation: Aggregation = aggregation
		self.percentile: float = percentile
		self.dtype: numpy.typing.DTypeLike = dtype
		self.infill: Infill = infill
		if percentile > 1.0 or percentile < 0:
			raise ValueError("Percentile out of range")
		if aggregation == Aggregation.LengthWeightedPercentile and percentile == 0:
			raise ValueError("Percentile argument should not be zero or omited when using a Percentile Aggregation")


def join_road_cwy(target: pd.DataFrame, data: pd.DataFrame, column_actions: list[Action]):
	# precalculate slk_length for each row of data
	data.loc[:, CN.slk_length] = data[CN.slk_to] - data[CN.slk_from]
	
	# reindex data for faster lookup
	data['merge_index'] = data.index
	data = data.set_index([CN.road_number, CN.carriageway, 'merge_index'])
	data = data.sort_index()
	# result_index = []
	# result_rows = []
	# result_index = numpy.empty(len(target.index), dtype="i4")
	
	result_columns = [
		numpy.empty(len(target.index), dtype=column_action.dtype) for column_action in column_actions
	]
	
	# Group target data by Road Number and Carriageway, loop over groups
	for (road_number, carriageway), target_group in target.groupby([CN.road_number, CN.carriageway]):
		try:
			data_matching_target_group = data.loc[(road_number, carriageway), :]
		except KeyError:
			continue
		
		last_target_index = None
		for target_index, target_row in target_group.iterrows():
			data_to_aggregate_for_target_group = data_matching_target_group[
				(data_matching_target_group[CN.slk_from] < target_row[CN.slk_to]) &
				(data_matching_target_group[CN.slk_to] > target_row[CN.slk_from])
			].copy()
			
			# if no data matches the target group do the infill strategy
			if len(data_to_aggregate_for_target_group.index) == 0:
				for column_action_index, column_action in enumerate(column_actions):
					if column_action.infill.type == InfillType.none:
						result_columns[column_action_index][target_index] = None
					elif column_action.infill.type == InfillType.value:
						result_columns[column_action_index][target_index] = column_action.infill.value
					# elif column_action.infill.type == InfillType.last:
					# 	if last_target_index:
					# 		result_columns[column_action_index][target_index] = result_columns[column_action_index][last_target_index]
					# 	# else:
					# 		# fatal? could not obtain last value
					else:
						raise Exception("unknown infill type")
				continue
			
			overlap_min = data_to_aggregate_for_target_group[CN.slk_from].apply(max, args=[target_row[CN.slk_from]])
			overlap_max = data_to_aggregate_for_target_group[CN.slk_to].apply(min, args=[target_row[CN.slk_to]])
			overlap_len = overlap_max - overlap_min
			# overlap_rat = overlap_len / data_to_aggregate_for_target_group[CN.slk_length]
			
			total_overlap_length = overlap_len.sum()
			
			#aggregated_result = []
			for column_action_index, column_action in enumerate(column_actions):
				if column_action.aggregation == Aggregation.LengthWeightedAverage:
					# aggregated_result.append(
					# 	(data_to_aggregate_for_target_group[column_action.column_name] * overlap_len / total_overlap_length).sum()
					# )
					result_columns[column_action_index][target_index] = (data_to_aggregate_for_target_group[column_action.column_name] * overlap_len / total_overlap_length).sum()
				elif column_action.aggregation == Aggregation.KeepLongest:
					# aggregated_result.append(
					# 	data_to_aggregate_for_target_group[column_action.column_name].loc[overlap_len.idxmax()]
					# )
					result_columns[column_action_index][target_index] = data_to_aggregate_for_target_group[column_action.column_name].loc[overlap_len.idxmax()]
				elif column_action.aggregation == Aggregation.LengthWeightedPercentile:
					# aggregated_result.append(
					# 	(data_to_aggregate_for_target_group[column_action.column_name] * overlap_len / total_overlap_length).quantile(column_action.percentile)
					# )
					result_columns[column_action_index][target_index] = (data_to_aggregate_for_target_group[column_action.column_name] * overlap_len / total_overlap_length).quantile(column_action.percentile)
				#result_index.append(target_index)
			#result_rows.append(aggregated_result)
			last_target_index = target_index
	
	column_action_names = [x.column_name for x in column_actions]
	return target.join(
		pd.DataFrame({
			column_action.column_name: column for column_action, column in zip(column_actions, result_columns)
		})
	)
