# dtimsprep<!-- omit in toc -->

- [1. Introduction](#1-introduction)
- [2. How to Use](#2-how-to-use)
  - [2.1. Option 1: install as editable package](#21-option-1-install-as-editable-package)
  - [2.2. Option 2: Copy Paste](#22-option-2-copy-paste)
  - [2.3. Option 3: From Wheel](#23-option-3-from-wheel)
- [3. Modules](#3-modules)
  - [3.1. Submodule Module `merge`](#31-submodule-module-merge)
    - [3.1.1. Merge Action (`merge.Action`)](#311-merge-action-mergeaction)
    - [3.1.2. Aggregation Type (`merge.Aggregation`)](#312-aggregation-type-mergeaggregation)
  - [3.2. Module `lookups`](#32-module-lookups)
  - [3.3. Module `timestamp`](#33-module-timestamp)
  - [3.4. Module `unit_conversion`](#34-module-unit_conversion)
- [4. Full Example](#4-full-example)

## 1. Introduction

`dtimsprep` is a pure python package which contains several modules useful in the
preparation of data for the dTIMS modelling process.

This package depends on Pandas (tested with version 1.3.1)

## 2. How to Use

### 2.1. Option 1: install as editable package

Clone this repo, then use the following command to install the package in "editable mode"

```bash
pip install -e .
```

### 2.2. Option 2: Copy Paste

Clone this repo, then copy-paste the `dtimsprep` folder from `./src/` into your python project directory, use as normal.

### 2.3. Option 3: From Wheel

In the future this package will be available in the "releases" section of github as a 'wheel'

## 3. Modules

### 3.1. Submodule Module `merge`

The merge module contains the main function `on_slk_intervals` as well as
several helper classes.

```python
import dtims_prep.merge

result = merge.on_slk_intervals(target, data, join_left, column_actions, from_to)
```

| Parameter      | Type                 | Note                                                                                                                                                                                                                                                                                                                                                                   |
| -------------- | -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| target         | `pandas.DataFrame`   | Slk segmentation of this file will be preserved in the result dataframe                                                                                                                                                                                                                                                                                                |
| data           | `pandas.DataFrame`   | Columns from this DataFrame will be aggregated to match the `target` slk segmentation and used to create new columns in the result dataframe                                                                                                                                                                                                                           |
| join_left      | `list[str]`          | This is the ordered list of column names to join with; Typically `["road_no","cway"]`. <ul><li>Must match in both the `target` and `data` DataFrames</li></ul>                                                                                                                                                                                                         |
| column_actions | `list[merge.Action]` | A list of `merge.Action()` objects describing the aggregation to be used for each column of data that is to be added to the target                                                                                                                                                                                                                                     |
| from_to        | `list[str]`          | the name of the start and end interval measures. Typically `["slk_from", "slk_to"]`  <ul><li>Must match in both the `target` and `data` DataFrames</li><li>should be converted to integers for reliable results prior to calling merge (see example below to see how the `unit_conversion.km_to_meters(s:pandas.Series)` function is used for this purpose.)</li></ul> |

> Note: The `merge.Action` and `merge.Aggregation` are described in the folowing sections.
> These classes exists to:
>
> - make calls to the merge function easier to read,
> - allow static type-checking and code hints
>   - Works best with PyCharm
>   - But VS Code + pylance are getting better

#### 3.1.1. Merge Action (`merge.Action`)

The `merge.Action` class is used to specify how a new column will be added to
the `target`.

Normally this would only ever be used as part of a call to the
`on_slk_intervals` function as shown below:

```python
import dtims_prep.merge

result = merge.on_slk_intervals(
    target=...,
    data=...,
    join_left=...,
    from_to=..., 
    column_actions = [
        merge.Action(column_name='column1', aggregation=merge.Aggregation.KeepLongest(), rename="column1_longest"),
        merge.Action('column1', merge.Aggregation.LengthWeightedAverage(), "column1_avg"),
        merge.Action('column2', merge.Aggregation.LengthWeightedPercentile()),
    ]
)

```

| Parameter   | Type                | Note                                                                                                                                         |
| ----------- | ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| column_name | `str`               | Name of column to aggregate in the `data` dataframe                                                                                          |
| aggregation | `merge.Aggregation` | One of the available merge aggregations described in the section below.                                                                      |
| rename      | `str`               | New name for aggregated column in the result dataframe. Note that this allows you to output multiple aggregations from a single input column |


#### 3.1.2. Aggregation Type (`merge.Aggregation`)

The following merge aggregations are supported:

| Constructor                                                   | Purpose                                                                                                                                    |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `merge.Aggregation.KeepLongest()`                             | Keep the longest non-blank value.                                                                                                          |
| `merge.Aggregation.LengthWeightedAverage()`                   | Compute the length weighted average of non-blank values                                                                                    |
| `merge.Aggregation.Average()`                                 | Compute the average non-blank value                                                                                                        |
| `merge.Aggregation.LengthWeightedPercentile(percentile=0.75)` | Compute the length weighted percentile (see description of method below). Value should be between 0.0 and 1.0. 0.75 means 75th percentile. |

### 3.2. Module `lookups`

Contains a class called `standard_column_names` which is meant to be used
instead of string literals when manipulating pandas dataframes.

```python
import pandas as pd
from dtimsprep.lookups import standard_column_names as CN

df1 = pd.read_csv("./some.csv")
df1 = df1.rename(columns={
    "ROAD":CN.road_number
})

df2 = pd.read_csv("./other.csv")
df2 = df2.rename(columns={
    "RoadNo":CN.road_number
})

# after renaming, you can reliably refer to the same field in both dataframes as below:
df1[CN.road_number]
df2[CN.road_number]
```

### 3.3. Module `timestamp`

Contains a convenience function for timestamping file outputs by prefixing a provided `filename` with
`YYYY MM DD HHMM filename`:

```python
import pandas as pd
from dtimsprep.timestamp import timestamp_filename

df = pd.DataFrame({
    "col1":[1,2,3],
    "col2":[3,4,5]
})

df.to_csv(timestamp_filename("important_data.csv"))
# Saves: `2021 05 08 1522 important_data.csv`
```

### 3.4. Module `unit_conversion`
contains a single function reproduced here in full:

```python
def km_to_meters(km: pandas.Series):
    """
    Converts a pandas Series object from floating point values to integer values, 
    multiplying by 1000.
    Fails if there are NaN or Inf values in the series."""
    return (km * 1000.0).round().astype('i4')
```

## 4. Full Example

```python
import pandas as pd
import dtims_prep.merge as merge
from dtims_prep.unit_conversion import km_to_meters

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
segmentation[[CN.slk_from, CN.slk_to]] = segmentation[[CN.slk_from,CN.slk_to]].apply(km_to_meters)

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
pavement_data[[CN.slk_from, CN.slk_to]] = pavement_data[[CN.slk_from, CN.slk_to]].apply(km_to_meters)

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

segmentation_pavement.to_csv(timestamp_filename("output.csv"))
```