# dtimsprep<!-- omit in toc -->

- [1. Introduction](#1-introduction)
- [2. Install, Upgrade, Uninstall](#2-install-upgrade-uninstall)
- [3. Module `merge`](#3-module-merge)
	- [3.1. Merge Action (`merge.Action`)](#31-merge-action-mergeaction)
	- [3.2. Aggregation Type (`merge.Aggregation`)](#32-aggregation-type-mergeaggregation)
		- [3.2.1. Notes: `Aggregation.KeepLongest()`](#321-notes-aggregationkeeplongest)
		- [3.2.2. Notes: `Aggregation.KeepLongestSegment()`](#322-notes-aggregationkeeplongestsegment)
- [4. Full Example](#4-full-example)

## 1. Introduction

`dtimsprep` is a pure python package which contains several modules useful in
the preparation of data for the dTIMS modelling process.

This package depends on Pandas (tested with version 1.3.1)

## 2. Install, Upgrade, Uninstall

To install:

```powershell
pip install "https://github.com/thehappycheese/dtimsprep/zipball/main/"
```

To Upgrade:

```powershell
pip install --upgrade "https://github.com/thehappycheese/dtimsprep/zipball/main"
```

To show installed version:

```powershell
pip show dtimsprep
```

To remove:

```powershell
pip uninstall dtimsprep
```



## 3. Module `merge`

The merge module contains the main function `on_slk_intervals` as well as
several helper classes.

```python
import dtimsprep.merge as merge

result = merge.on_slk_intervals(target, data, join_left, column_actions, from_to)
```

| Parameter      | Type                 | Note                                                                                                                                                                                                                                                                                                                                                                                      |
| -------------- | -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| target         | `pandas.DataFrame`   | The result will have the same number of rows as the `target` data frame, and each row of the result will match the slk_interval of the target.                                                                                                                                                                                                                                            |
| data           | `pandas.DataFrame`   | Columns from this DataFrame will be aggregated to match the `target` slk segmentation and used to create new columns in the result dataframe                                                                                                                                                                                                                                              |
| join_left      | `list[str]`          | Ordered list of column names to join with.<br>Typically `["road_no","cway"]`.<br>Note:<ul><li>These column names must match in both the `target` and `data` DataFrames</li></ul>                                                                                                                                                                                                          |
| column_actions | `list[merge.Action]` | A list of `merge.Action()` objects describing the aggregation to be used for each column of data that is to be added to the target. See examples below.                                                                                                                                                                                                                                   |
| from_to        | `list[str]`          | the name of the start and end interval measures.<br>Typically `["slk_from", "slk_to"]`.<br>Note:<ul><li>These column names must match in both the `target` and `data` DataFrames</li><li>These columns should be converted to integers for reliable results prior to calling merge (see example below. The `unit_conversion.km_to_meters()` function is used for this purpose.)</li></ul> |

### 3.1. Merge Action (`merge.Action`)

The `merge.Action` class is used to specify how a new column will be added to
the `target`.

Normally this would only ever be used as part of a call to the
`on_slk_intervals` function as shown below:

```python
import dtimsprep.merge as merge

result = merge.on_slk_intervals(
    ..., 
    column_actions = [
        merge.Action(column_name="column1", aggregation=merge.Aggregation.KeepLongest(), rename="column1_longest"),
        merge.Action("column1", merge.Aggregation.LengthWeightedAverage(), "column1_avg"),
        merge.Action("column2", merge.Aggregation.LengthWeightedPercentile(0.75)),
    ]
)

```

| Parameter   | Type                | Note                                                                                                                                                          |
| ----------- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| column_name | `str`               | Name of column to aggregate in the `data` dataframe                                                                                                           |
| aggregation | `merge.Aggregation` | One of the available merge aggregations described in the section below.                                                                                       |
| rename      | `Optional[str]`     | New name for aggregated column in the result dataframe. Note that this allows you to output multiple aggregations from a single input column. Can be omitted. |

### 3.2. Aggregation Type (`merge.Aggregation`)

The following merge aggregations are supported:

| Constructor                                                   | Purpose                                                                                                                                    |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `merge.Aggregation.First()`                                   | Keep the first non-blank value.                                                                                                            |
| `merge.Aggregation.KeepLongest()`                             | Keep the longest non-blank value. see notes below                                                                                          |
| `merge.Aggregation.LengthWeightedAverage()`                   | Compute the length weighted average of non-blank values                                                                                    |
| `merge.Aggregation.Average()`                                 | Compute the average non-blank value                                                                                                        |
| `merge.Aggregation.LengthWeightedPercentile(percentile=0.75)` | Compute the length weighted percentile (see description of method below). Value should be between 0.0 and 1.0. 0.75 means 75th percentile. |

#### 3.2.1. Notes about `Aggregation.KeepLongest()`

`KeepLongest()` works by observing both the segment lenghts and segment values
for data rows matching a particular target segment.

**Note 1:** If all segments are the same length, then the first segment to
appear in the data input table will be selected.

```
Target Segment:       |===========================|
Data Segments:        |==33==|==55==|==66==|==77==|
KeepLongestSegment:      33
```

**Note 2:** If the data to be merged has several short segments with the same
value, which together form the 'longest' value then this longest value will be
selected. For example in the situation below the data segement `55` is the
longest individual segment, but `99` is the longest value. The result is
therefore `99`.

```
Target Segment:          |==============================|
Data segment:      |=======55=======|==99==|==99==|==99==|==11==|
KeepLongest:                           99
```


## 4. Full Example

```python
import pandas as pd
import dtimsprep.merge as merge

# =====================================================
# Use a data class to hold some standard column names
# =====================================================
class CN:
    road_number = "road_no"
    carriageway = "cway"
    segment_name = "seg_name"
    slk_from = "slk_from"
    slk_to = "slk_to"
    pavement_total_width = "PaveW"
    pavement_year_constructed = "PaveY"

# =====================================================
# load target segmentation
# =====================================================
segmentation = pd.read_csv("network_segmentation.csv")

# Rename columns to our standard names:
segmentation = segmentation.rename(columns={
    "RoadName":     CN.road_number,
    "Cway":         CN.carriageway,
    "Name":         CN.segment_name,
    "From":         CN.slk_from,
    "To":           CN.slk_to
})

# Drop rows where critical fields are blank
segmentation = segmentation.dropna(subset=[CN.road_number, CN.carriageway, CN.slk_from, CN.slk_to])

# Convert SLKs to meters and round to integer
segmentation[CN.slk_from] = (segmentation[CN.slk_from]/1000.0).astype("int")
segmentation[CN.slk_to] = (segmentation[CN.slk_to]/1000.0).astype("int")

# =====================================================
# load data to be merged
# =====================================================
pavement_data = pd.read_csv("pavement_details.csv")

# Rename columns to our standard names:
pavement_data = pavement_data.rename(columns={
    "ROAD_NO":          CN.road_number,
    "CWY":              CN.carriageway,
    "START_SLK":        CN.slk_from,
    "END_SLK":          CN.slk_to,
    "TOTAL_WIDTH":      CN.pavement_total_width,
    "PAOR_PAVE_YEAR":   CN.pavement_year_constructed,
})

# Drop rows where critical fields are blank
pavement_data = pavement_data.dropna(subset=[CN.road_number, CN.carriageway, CN.slk_from, CN.slk_to])

# Convert SLKs to meters and round to integer
pavement_data[CN.slk_from] = (pavement_data[CN.slk_from]/1000.0).astype("int")
pavement_data[CN.slk_to] = (pavement_data[CN.slk_to]/1000.0).astype("int")

# =====================================================
# Execute the merge:
# =====================================================

segmentation_pavement = merge.on_slk_intervals(
    target=segmentation,
    data=pavement_data,
    join_left=[CN.road_number, CN.carriageway],
    column_actions=[
        merge.Action(CN.pavement_total_width,        merge.Aggregation.LengthWeightedAverage()),
        merge.Action(CN.pavement_year_constructed,   merge.Aggregation.KeepLongest())
    ],
    from_to=[CN.slk_from, CN.slk_to]
)

segmentation_pavement.to_csv("output.csv")
```