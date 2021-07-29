from typing import Any, Optional
from enum import Enum
import pandas as pd
import numpy as np

from .lookups import standard_column_names as CN


class AggregationType(Enum):
	KeepLongest = 1
	Average = 2
	LengthWeightedAverage = 3
	LengthWeightedPercentile = 4

class Aggregation:

	def __init__(self, aggregation_type:AggregationType, percentile:Optional[float] = None):
		"""Don't use initialise this class directly, please use one of the static factory functions above"""
		self.type:AggregationType = aggregation_type
		self.percentile:Optional[float] = percentile
		pass

	@staticmethod
	def KeepLongest():
		return Aggregation(AggregationType.KeepLongest)

	@staticmethod
	def LengthWeightedAverage():
		return Aggregation(AggregationType.LengthWeightedAverage)
	
	@staticmethod
	def Average():
		return Aggregation(AggregationType.Average)

	@staticmethod
	def LengthWeightedPercentile(percentile:float):
		if percentile > 1.0 or percentile < 0.0:
			raise ValueError(
				f"Percentile out of range. Must be greater than 0.0 and less than 1.0. Got {percentile}." +
				(" Did you need to divide by 100?" if percentile>1.0 else "")
			)
		return Aggregation(
			AggregationType.LengthWeightedPercentile,
			percentile=percentile
		)


class InfillType(Enum):
	none = 1
	value = 2


class Infill:
	def __init__(self, infill_type:InfillType, value:Optional[Any]):
		"""don't initialise directly, use the static builder methods"""
		self.type: InfillType = infill_type
		self.value:Optional[Any] = value
	
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
			infill: Infill = Infill.none()
	):
		self.column_name: str = column_name
		self.aggregation: Aggregation = aggregation
		self.infill: Infill = infill
		


def on_slk_intervals(target: pd.DataFrame, data: pd.DataFrame, join_left: list[str], column_actions: list[Action]):
	result_index = []
	result_rows = []
	
	# precalculate slk_length for each row of data
	# data.loc[:, CN.slk_length] = data[CN.slk_to] - data[CN.slk_from]
	
	# reindex data for faster lookup
	# data['merge_index'] = data.index
	# data = data.set_index([*join_left, 'merge_index'])
	# data = data.sort_index()
	


	# Group target data by Road Number and Carriageway
	try:
		target_groups = target.groupby(join_left)
	except KeyError as e:
		matching_columns = [col for col in join_left if col in target.columns]
		raise Exception(f"Parameter join_left={join_left} did not match" + (
			" any columns in the target DataFrame" if len(matching_columns)==0
			else f" all columns in target DataFrame. Only matched columns {matching_columns}"
		))
		

	for target_group_index, target_group in target_groups:
		# try:
		# 	data_matching_target_group = data.loc[target_group_index, :]
		# except KeyError:
		# 	# There was no data matching the target group 
		# 	continue
		# except TypeError as e:
		# 	# The datatype of target_group_index is picky... sometimes it wants a tuple, sometimes it will accept a list
		# 	# this appears to be a bug or inconsistency with pandas when using multi-index dataframes.
		# 	print(f"Error: Could not group the following data by {target_group_index}:")
		# 	print(data)
		# 	data_matching_target_group = data.loc[list(target_group_index), :]
		# 	raise e

		# I abandoned multi indexed data frames because they appear to be either 1) broken, 2) poorly documented;
		# sometimes you can slice them with a list of column names, other times it only works with a tuple.
		# I think this is because sometimes target_group is a series and sometimes it is a dataframe.

		# the method used below to filter the data may not be the fastest
		data_matching_target_group = data
		for index_value, index_column_name in zip(target_group_index, join_left):
			data_matching_target_group = data_matching_target_group[data_matching_target_group[index_column_name]==index_value]
		
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
			overlap_min = np.maximum(data_to_aggregate_for_target_group[CN.slk_from], target_row[CN.slk_from])
			overlap_max = np.minimum(data_to_aggregate_for_target_group[CN.slk_to],   target_row[CN.slk_to])

			overlap_len = overlap_max - overlap_min
			
			# the sum of the length of all data segments overlapping the target segment
			total_overlap_length = overlap_len.sum()
			
			# for each column of data that we keep, we must aggregate each field down to a single value
			aggregated_result = []
			for column_action_index, column_action in enumerate(column_actions):

				# TODO: there is a bug here; we need to do data_to_aggregate_for_target_group[column_action.column_name].dropna()
				# but we can't because we would need to also drop the corresponding overlap_len and recompute total_overlap_length for each column action.

				if column_action.aggregation.type == AggregationType.LengthWeightedAverage:
					aggregated_result.append(
						(data_to_aggregate_for_target_group[column_action.column_name] * overlap_len ).sum() / total_overlap_length
					)
				
				elif column_action.aggregation.type == AggregationType.KeepLongest:
					aggregated_result.append(
						data_to_aggregate_for_target_group[column_action.column_name].loc[overlap_len.idxmax()]
					)
				
				elif column_action.aggregation.type == AggregationType.LengthWeightedPercentile:
					
					values_and_lengths = pd.DataFrame([
							data_to_aggregate_for_target_group[column_action.column_name],
							overlap_len
						],
						columns=["values","lengths"]
					).sort_values(by="values")
					x_coords = (values_and_lengths["lengths"].rolling(2).mean()).fillna(0).cumsum()
					x_coords/=x_coords.iloc[-1]
					result = np.interp(
						column_action.aggregation.percentile,
						x_coords.to_numpy(),
						values_and_lengths["values"].to_numpy()
					)
					aggregated_result.append(result)
					

					# aggregated_result.append(
					# 	(data_to_aggregate_for_target_group[column_action.column_name] * overlap_len / total_overlap_length).quantile(column_action.aggregation.percentile)
					# )
			result_index.append(target_index)
			result_rows.append(aggregated_result)
	
	return target.join(
		pd.DataFrame(
			result_rows,
			columns=[x.column_name for x in column_actions],
			index=result_index
		)
	)
