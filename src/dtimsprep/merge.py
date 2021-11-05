from enum import Enum
from typing import Optional, List, Tuple

import numpy as np
import pandas
import pandas as pd


class AggregationType(Enum):
	KeepLongestSegment = 1  # Deprecated
	KeepLongest = 2
	Average = 3
	LengthWeightedAverage = 4
	LengthWeightedPercentile = 5
	First = 6
	ProportionalSum = 7
	Sum = 8
	IndexOfMax = 9


class Aggregation:
	
	def __init__(self, aggregation_type: AggregationType, percentile: Optional[float] = None):
		"""Don't use initialise this class directly, please use one of the static factory functions above"""
		self.type: AggregationType = aggregation_type
		self.percentile: Optional[float] = percentile
		pass
	
	@staticmethod
	def First():
		return Aggregation(AggregationType.First)
	
	@staticmethod
	def KeepLongestSegment():
		print("WARNING KeepLongestSegment is deprecated please do not use this function. it is kept here for testing but is to be removed in future versions.")
		return Aggregation(AggregationType.KeepLongestSegment)
	
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
	def LengthWeightedPercentile(percentile: float):
		if percentile > 1.0 or percentile < 0.0:
			raise ValueError(
				f"Percentile out of range. Must be greater than 0.0 and less than 1.0. Got {percentile}." +
				(" Do you need to divide by 100?" if percentile > 1.0 else "")
			)
		return Aggregation(
			AggregationType.LengthWeightedPercentile,
			percentile=percentile
		)
	
	@staticmethod
	def ProportionalSum():
		"""This is the sum of values overlapping the target segment; The value of each segment is multiplied by the proportion of that segment overlapping the target segment."""
		return Aggregation(AggregationType.ProportionalSum)

	@staticmethod
	def Sum():
		"""This is the sum of values touching the target. Even if only part of the value is overlapping the target segment, the entire data value will be added to the sum"""
		return Aggregation(AggregationType.Sum)

	@staticmethod
	def IndexOfMax():
		"""This is the row label of the maximum value detected in the data"""
		return Aggregation(AggregationType.IndexOfMax)

	# @staticmethod
	# def SumLengthWeightedAveragePerCategory(category_column_name:str):
	# 	"""For the set of data matching a target row, get the length weighted average for each category, then sum the results."""
	# 	return Aggregation(AggregationType.IndexOfMax)

class Action:
	def __init__(
			self,
			column_name: str,
			aggregation: Aggregation,
			rename: Optional[str] = None
	):
		self.column_name: str = column_name
		self.rename = rename if rename is not None else self.column_name
		self.aggregation: Aggregation = aggregation


def on_slk_intervals(target: pd.DataFrame, data: pd.DataFrame, join_left: List[str], column_actions: List[Action], from_to: Tuple[str, str] = ("slk_from", "slk_to")):
	slk_from, slk_to = from_to
	
	result_index = []
	result_rows = []

	if not isinstance(join_left, list):
		raise Exception("Parameter `join_left` must be a list literal. Tuples and other sequence types will lead to cryptic errors from pandas.")
	
	# ReIndex data for faster O(N) lookup
	data = data.assign(data_id=data.index)
	data = data.set_index([*join_left, 'data_id'])
	data = data.sort_index()
	
	# Group target data by Road Number and Carriageway
	try:
		target_groups = target.groupby(join_left)
	except KeyError:
		matching_columns = [col for col in join_left if col in target.columns]
		raise Exception(f"Parameter join_left={join_left} did not match" + (
			" any columns in the target DataFrame" if len(matching_columns) == 0
			else f" all columns in target DataFrame. Only matched columns {matching_columns}"
		))
	
	# Main Loop
	for target_group_index, target_group in target_groups:
		try:
			data_matching_target_group = data.loc[target_group_index]
		except KeyError:
			# There was no data matching the target group. Skip adding output. output to these rows will be NaN for all columns.
			continue
		except TypeError as e:
			# The datatype of group_index is picky... sometimes it wants a tuple, sometimes it will accept a list
			# this appears to be a bug or inconsistency with pandas when using multi-index dataframes.
			print(f"Error: Could not group the following data by {target_group_index}:")
			print(f"type(group_index)  {type(target_group_index)}:")
			print("the data:")
			print(data)
			raise e
		
		# Iterate row by row through the target group
		for target_index, target_row in target_group.iterrows():
			
			# Select data with overlapping slk interval
			data_to_aggregate_for_target_group = data_matching_target_group[
				(data_matching_target_group[slk_from] < target_row[slk_to]) &
				(data_matching_target_group[slk_to] > target_row[slk_from])
			]#.copy()
			# TODO: the copy function on the line above has a lot to do with the slowness of this algorithm
			#       because all columns are copied, not just the ones we are aggregating, for wide dataframes
			#       there is potentially a huge amount of memory allocated and deallocated that doesnt need to be.
			#       only needs to be copied so that the "overlap_len" column can be added. If we can avoid adding
			#       this column we might do a lot better.
			
			# if no data matches the target group then skip
			if data_to_aggregate_for_target_group.empty:
				continue
			
			# compute overlaps for each row of data
			overlap_min = np.maximum(data_to_aggregate_for_target_group[slk_from], target_row[slk_from])
			overlap_max = np.minimum(data_to_aggregate_for_target_group[slk_to],   target_row[slk_to])
			
			# overlap_len = np.maximum(overlap_max - overlap_min, 0)  # np.maximum() is not needed due to filters above
			overlap_len = overlap_max - overlap_min
			
			# expect this to trigger warning about setting value on view?
			# does not seem to though
			#data_to_aggregate_for_target_group["overlap_len"] = overlap_len  # Remove this... there is no reason to attached overlap_len to the original dataframe
			
			# for each column of data that we keep, we must aggregate each field down to a single value
			# create a blank row to store the result of each column
			aggregated_result_row = []
			for column_action_index, column_action in enumerate(column_actions):

				column_len_to_aggregate: pd.DataFrame = (
					data_to_aggregate_for_target_group
					.loc[:, [column_action.column_name]]
					.assign(overlap_len=overlap_len)  # assign is done here so that NaN data can be dropped at the same time as the overlap lengths. Later we also benefit from the combination by being able to concurrently sort both columns.
				)
				column_len_to_aggregate = column_len_to_aggregate[
					~ column_len_to_aggregate.iloc[:, 0].isna() &
					  (column_len_to_aggregate["overlap_len"] > 0)
				]
				
				if column_len_to_aggregate.empty:
					# Infill with np.nan or we will lose our column position.
					aggregated_result_row.append(np.nan)
					continue
				
				column_to_aggregate:             pandas.Series = column_len_to_aggregate.iloc[:, 0]
				column_to_aggregate_overlap_len: pandas.Series = column_len_to_aggregate.iloc[:, 1]
				
				if column_action.aggregation.type   == AggregationType.Average:
					aggregated_result_row.append(
						column_to_aggregate.mean()
					)
					
				elif column_action.aggregation.type == AggregationType.First:
					aggregated_result_row.append(column_to_aggregate.iloc[0])
				
				elif column_action.aggregation.type == AggregationType.LengthWeightedAverage:
					total_overlap_length = column_to_aggregate_overlap_len.sum()
					aggregated_result_row.append(
						(column_to_aggregate * column_to_aggregate_overlap_len).sum() / total_overlap_length
					)

				elif column_action.aggregation.type == AggregationType.KeepLongestSegment:
					aggregated_result_row.append(
						column_to_aggregate.loc[column_to_aggregate_overlap_len.idxmax()]
					)

				elif column_action.aggregation.type == AggregationType.KeepLongest:
					aggregated_result_row.append(
						column_to_aggregate_overlap_len.groupby(column_to_aggregate).sum().idxmax()
					)

				elif column_action.aggregation.type == AggregationType.LengthWeightedPercentile:
					column_len_to_aggregate = column_len_to_aggregate.sort_values(
						by=column_action.column_name,
						ascending=True
					)

					column_to_aggregate:             pandas.Series = column_len_to_aggregate.iloc[:, 0] # TODO: Why is this repeated?
					column_to_aggregate_overlap_len: pandas.Series = column_len_to_aggregate.iloc[:, 1] # TODO: Why is this repeated?
					
					x_coords = (column_to_aggregate_overlap_len.rolling(2).mean()).fillna(0).cumsum()
					x_coords /= x_coords.iloc[-1]
					result = np.interp(
						column_action.aggregation.percentile,
						x_coords.to_numpy(),
						column_to_aggregate
					)
					aggregated_result_row.append(result)

				elif column_action.aggregation.type == AggregationType.ProportionalSum:
					# total_overlap_length = column_to_aggregate_overlap_len.sum()
					data_to_aggregate_for_target_group_slk_length = data_to_aggregate_for_target_group[slk_to]-data_to_aggregate_for_target_group[slk_from]
					aggregated_result_row.append(
						(column_to_aggregate * column_to_aggregate_overlap_len/data_to_aggregate_for_target_group_slk_length).sum()
					)
				
				elif column_action.aggregation.type == AggregationType.Sum:
					aggregated_result_row.append(
						column_to_aggregate.sum()
					)

				elif column_action.aggregation.type == AggregationType.IndexOfMax:
					aggregated_result_row.append(
						column_to_aggregate.idxmax()
					)
				
				# elif column_action.aggregation.type == AggregationType.SumMaxPerCategory:
				# 	column_to_aggregate.index
			
			result_index.append(target_index)
			result_rows.append(aggregated_result_row)
	
	return target.join(
		pd.DataFrame(
			result_rows,
			columns=[x.rename for x in column_actions],
			index=result_index
		)
	)
