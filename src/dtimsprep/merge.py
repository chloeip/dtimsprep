from collections import Counter
from enum import Enum
from typing import Optional, List, Tuple

import numpy as np
import pandas
import pandas as pd


class AggregationType(Enum):
	KeepLongestSegment = 1
	KeepLongestValue = 6
	Average = 2
	LengthWeightedAverage = 3
	LengthWeightedPercentile = 4
	First = 5


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
		return Aggregation(AggregationType.KeepLongestSegment)
	
	@staticmethod
	def KeepLongestValue():
		return Aggregation(AggregationType.KeepLongestValue)
	
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
	
	# reindex data for faster lookup
	data['data_id'] = data.index
	data = data.set_index([*join_left, 'data_id'])
	data = data.sort_index()
	# Group target data by Road Number and Carriageway
	try:
		target_groups = target.groupby(join_left)
	except KeyError as _e:
		matching_columns = [col for col in join_left if col in target.columns]
		raise Exception(f"Parameter join_left={join_left} did not match" + (
			" any columns in the target DataFrame" if len(matching_columns) == 0
			else f" all columns in target DataFrame. Only matched columns {matching_columns}"
		))
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
			].copy()
			
			# if no data matches the target group then skip
			if data_to_aggregate_for_target_group.empty:
				continue
			
			# compute overlaps for each row of data
			overlap_min = np.maximum(data_to_aggregate_for_target_group[slk_from], target_row[slk_from])
			overlap_max = np.minimum(data_to_aggregate_for_target_group[slk_to], target_row[slk_to])
			
			# overlap_len = np.maximum(overlap_max - overlap_min, 0)
			overlap_len = overlap_max - overlap_min
			
			# expect this to trigger warning ?
			data_to_aggregate_for_target_group["overlap_len"] = overlap_len
			
			# for each column of data that we keep, we must aggregate each field down to a single value
			# create a blank row to store the result of each column
			aggregated_result_row = []
			for column_action_index, column_action in enumerate(column_actions):
				column_len_to_aggregate: pd.DataFrame = data_to_aggregate_for_target_group.loc[:, [column_action.column_name, "overlap_len"]]
				column_len_to_aggregate = column_len_to_aggregate[
					~column_len_to_aggregate.iloc[:, 0].isna() &
					(column_len_to_aggregate["overlap_len"] > 0)
				]
				
				if column_len_to_aggregate.empty:
					# Infill with none or we will lose our column position.
					aggregated_result_row.append(None)
					continue
				
				column_to_aggregate: pandas.Series = column_len_to_aggregate.iloc[:, 0]
				column_to_aggregate_overlap_len: pandas.Series = column_len_to_aggregate.iloc[:, 1]
				
				if column_action.aggregation.type == AggregationType.Average:
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
					
				elif column_action.aggregation.type == AggregationType.KeepLongestValue:
					
					aa = column_to_aggregate_overlap_len.groupby(column_to_aggregate).sum().idxmax()
					aggregated_result_row.append(aa)
					
				elif column_action.aggregation.type == AggregationType.LengthWeightedPercentile:
					
					column_len_to_aggregate = column_len_to_aggregate.sort_values(
						by=column_action.column_name,
						ascending=True
					)
					
					column_to_aggregate = column_len_to_aggregate.iloc[:, 0]
					column_to_aggregate_overlap_len = column_len_to_aggregate.iloc[:, 1]
					
					x_coords = (column_to_aggregate_overlap_len.rolling(2).mean()).fillna(0).cumsum()
					x_coords /= x_coords.iloc[-1]
					result = np.interp(
						column_action.aggregation.percentile,
						x_coords.to_numpy(),
						column_to_aggregate
					)
					aggregated_result_row.append(result)
			
			result_index.append(target_index)
			result_rows.append(aggregated_result_row)
	
	return target.join(
		pd.DataFrame(
			result_rows,
			columns=[x.rename for x in column_actions],
			index=result_index
		)
	)
