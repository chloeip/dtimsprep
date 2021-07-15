

class standard_column_names:
	"""lookup table for standard dTIMS input column names
	By using this class like
	>>> from lookups import standard_column_names as CN
	You get nice autocomplete hints when typing `CN.`
	"""
	segment_name = "seg_name"
	road_number = "road_no"
	carriageway = "cway"
	slk_from = "slk_from"
	slk_to = "slk_to"
	slk_length = "slk_length"
	xsp = "xsp"
	pavement_total_width = "F_Wdth"
	pavement_year_constructed = "PaveYr"