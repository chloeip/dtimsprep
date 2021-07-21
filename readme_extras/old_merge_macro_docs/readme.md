# Merge Tool <!-- omit in toc -->
- [1. Aggregation ("Transformation") Types](#1-aggregation-transformation-types)
	- [1.1. Average Plus Multiple of Standard Deviation](#11-average-plus-multiple-of-standard-deviation)
	- [1.2. Length-Weighted Average Plus Multiple of Standard Deviation](#12-length-weighted-average-plus-multiple-of-standard-deviation)
	- [1.3. Percentile](#13-percentile)
	- [1.4. Length-weighted Percentile](#14-length-weighted-percentile)
	- [1.5. Keep First](#15-keep-first)
	- [1.6. Keep Last](#16-keep-last)
	- [1.7. Keep Longest](#17-keep-longest)
	- [1.8. Minimum](#18-minimum)
	- [1.9. Maximum](#19-maximum)
	- [1.10. Sum](#110-sum)
	- [1.11. Linear](#111-linear)


## 1. Aggregation ("Transformation") Types

> **Nicks Notes**: The following documentation has been lifted from the excel merge tool. Minor wording changes made for clarity, but meaning left unchanged.

### 1.1. Average Plus Multiple of Standard Deviation

```text
1 , [Percent of StdDev] , [keep StdDev] , [Capping]
```

Computes the average then adds some multiple of the standard deviation.

- `[Percent of StdDev]`: Percentage of the Standard Deviation of the data falling within a location that is added to the Average.  Eg: a value of 50 will cause 50% of the Std Dev to be added to the Average
- `[keep StdDev]`: a value of `1` will cause the Standard Deviation to be written (kept) as well.
- `[Capping]`: a value of `1` Enables capping (upper and lower) to the highest or lowest value found.

>If only portion of a length of data falls within a location, then that data point will be included in the Average.

### 1.2. Length-Weighted Average Plus Multiple of Standard Deviation

```text
2 , [Percent of StdDev] , [keep StdDev] , [Capping]
```

Computes the length-weighted average then adds some multiple of the standard deviation.

- `[Percent of StdDev]`: Percentage of the Standard Deviation of the data falling within a location that is added to the Average.  Eg: a value of 50 will cause 50% of the Std Dev to be added to the Average
- `[keep StdDev]`: a value of `1` will cause the Standard Deviation to be written (kept) as well.
- `[Capping]`: a value of `1` Enables capping (upper and lower) to the highest or lowest value found.

> If all the data are in equal lengths, then Length-Weighting gives the same answers as the normal un-weighted averages.

> If only portion of a length of data falls within a location, then the length used in the weighting is only that length that falls within the location.

### 1.3. Percentile

```text
3 , [Percentile]
```

- `[Percentile]`: Percentile to compute. For example `3, 75` will calculate the 75th percentiles.


### 1.4. Length-weighted Percentile

```text
4 , [Percentile]
```

- `[Percentile]`: Percentile to compute. For example `4, 75` will calculate the 75th percentiles.

> Length-weighting is applied to the data when finding the percentile values. This is practical if the data is in variable lengths.
 
> If all the data segments are of equal length, then Length-Weighting gives the same answers as the normal un-weighted percentiles.

### 1.5. Keep First

```text
5
```

The first data value that falls within or partly within the location section.

### 1.6. Keep Last

The last data value that falls within or partly within the location section.

```text
6
```

### 1.7. Keep Longest

The data value that has the most length, falling within the location section, is
kept. This would normally be used for text fields, but will also work with
numerical data. Allowance has been made for the possibility that the lengths may
be fragmented. Example: you may wish to know the Road Class [M, A, B, C, D] that
has the most length. The lengths of road falling into each class are summed into
an array of Road Class, and then the most length calculation is made on the
resultant array.

```text
7
```

### 1.8. Minimum

The lowest data value falling partly or completely into the location section.

```text
8
```

### 1.9. Maximum

The highest data value falling partly or completely into the location section.

```text
9
```

### 1.10. Sum

Data values falling within a location section are summed.  If only a portion of a data value falls within a location section, then the data is prorated.  Example: if 30% of the data section falls within a location section, then only 30% of that data value is summed."

```text
10
```

### 1.11. Linear

Used to merge a second pair of distance fields.
If you have chosen the option, "Common fields have different names", then merged distances will be multiplied by the "Distance Multiplier"

```text
11
```

> **Nicks Notes**: Option 11 makes not sense at all :O