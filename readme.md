# dTIMS Preparation<!-- omit in toc -->

- [1. Modules](#1-modules)
	- [1.1. Module `lookups`](#11-module-lookups)
	- [1.2. Module `merge`](#12-module-merge)
	- [1.3. Aggregation Type (`merge.Aggregation`)](#13-aggregation-type-mergeaggregation)
	- [1.4. Infill Type (`merge.Infill`)](#14-infill-type-mergeinfill)
- [2. Example:](#2-example)

## 1. Modules

### 1.1. Module `lookups`

Contains a class called `standard_column_names` which is meant to be used
instead of string literals when manipulating pandas dataframes.

```python
import pandas as pd
from dtims_prep.lookups import standard_column_names as CN

df1 = pd.read_csv("./some.csv")
df1 = df1.rename(columns={
    "ROAD":CN.road_number
})

df2 = pd.read_csv("./other.csv")
df2 = df2.rename(columns={
    "RoadNo":CN.road_number
})

df1[CN.road_number]
df2[CN.road_number]
```

### 1.2. Module `merge`

The merge module contains the main function `on_slk_intervals` as well as
several helper classes.

```python
import dtims_prep.merge

result = merge.on_slk_intervals(
	target: pandas.DataFrame,           # slk segmentation of this file will be preserved
	data: pandas.DataFrame,             # columns from this DataFrame will be aggregated to match the target slk segmentation
	join_left: list[str],               # This is the ordered list of column names to join with; normally ["ROAD","CWY"]
	column_actions: list[merge.Action]  # A list of merge.Action() objects describing the aggregation to be used for each column of data that is to be added to the target
	infill: merge.Infill
)
```

Note:

- column names nominated by the `join_left` parameter must match in both the
  `target` and `data` DataFrames
- columns `slk_from` and `slk_to`
  - must match `lookups.standard_column_names.slk_from` and
    `lookups.standard_column_names.slk_to`,
  - must be the same in both dataframes
  - should optionally be converted to integers and measured in meters for
    reliable results prior to calling merge
- slk is used rather than true distance

The `merge.Action`, `merge.Aggregation`, and `merge.Infill` classes exists to make calls the the merge function

- easier to read,
- statically type-checkable and
- allow IDEs to provide good hints
  - Works best with PyCharm
  - But VS Code + pylance are getting better at a rapid pace

### 1.3. Aggregation Type (`merge.Aggregation`)

The following merge actions are currently supported
| Constructor                                                   | Purpose                                                                                                                                    |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `merge.Aggregation.KeepLongest()`                             | Keep the longest non-blank value.                                                                                                          |
| `merge.Aggregation.LengthWeightedAverage()`                   | Compute the length weighted average of non-blank values                                                                                    |
| `merge.Aggregation.Average()`                                 | Compute the average non-blank value                                                                                                        |
| `merge.Aggregation.LengthWeightedPercentile(percentile=0.75)` | Compute the length weighted percentile (see description of method below). Value should be between 0.0 and 1.0. 0.75 means 75th percentile. |

### 1.4. Infill Type (`merge.Infill`)

Where all data corresponding with a target value is blank, the following
strategies are available to infill the value:

| Constructor                   | Purpose                                      |
| ----------------------------- | -------------------------------------------- |
| `merge.Infill.value(value=0)` | Infill the output with the provided `value`. |
| `merge.Infill.none()`         | Infill the output with `None` or `numpy.nan` |

## 2. Example:

```python
import pandas as pd
from dtims_prep.lookups import standard_column_names as CN
import dtims_prep.merge as merge
from dtims_prep.unit_conversion import km_to_meters

# =====================================================
# load target segmentation
# =====================================================
seg_cwy = pd.read_csv("network_segmentation.csv")

# define column name map
seg_cwy_column_name_map = {
    "RoadName":     CN.road_number,
    "Cway":         CN.carriageway,
    "Name":         CN.segment_name,
    "From":         CN.slk_from,
    "To":           CN.slk_to
}

# Rename columns
seg_cwy = seg_cwy.rename(columns=seg_cwy_column_name_map)

# Convert SLKs to meters and round to integer
seg_cwy[[CN.slk_from, CN.slk_to]] = seg_cwy[[CN.slk_from,CN.slk_to]].apply(km_to_meters)

# =====================================================
# load data to be merged
# =====================================================
pav = pd.read_csv("pavement_details.csv")

pav_map = {
    "ROAD_NO":          CN.road_number,
    "CWY":              CN.carriageway,
    "START_SLK":        CN.slk_from,
    "END_SLK":          CN.slk_to,
    "TOTAL_WIDTH":      CN.pavement_total_width,
    "PAOR_PAVE_YEAR":   CN.pavement_year_constructed,
}

# Drop unused columns
pav = pav.loc[:,list(pav_map.keys())]

# Rename columns
pav = pav.rename(columns=pav_map)

# Drop rows where the road_number or carriageway fields are blank
pav = pav.dropna(subset=[CN.road_number, CN.carriageway])

# Convert SLKs to meters and round to integer
pav[[CN.slk_from, CN.slk_to]] = pav[[CN.slk_from, CN.slk_to]].apply(km_to_meters)

# =====================================================
# Execute the merge:
# =====================================================

seg_cwy_pav = merge.on_slk_intervals(
    target=seg_cwy,
    data=pav,
    join_left=[CN.road_number, CN.carriageway],
    column_actions=[
        merge.Action(CN.pavement_total_width,        merge.Aggregation.LengthWeightedAverage(), infill=merge.Infill.none()),
        merge.Action(CN.pavement_year_constructed,   merge.Aggregation.KeepLongest(),           infill=merge.Infill.none())
    ]
)
```