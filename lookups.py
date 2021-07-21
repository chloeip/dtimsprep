


class Printable_Class_Members(type):
	""" This metaclass alters the way that python prints another class
	Normally when you create a class like this and try to print it:
	```
	class ExampleClass:
		some_prop = "some_value"
		another_prop = "another_value"
	
	print(ExampleClass)
	```

	you get something unintelligible like `<class '__main__.ExampleClass'>`
	by adding this metaclass like this;
	```
	class ExampleClass(metaclass=Printable_Class_Members):
		some_prop = "some_value"
		another_prop = "another_value"
	
	print(ExampleClass)
	```
	you get
	```
	```

	"""
	def __repr__(self):
		return str(self)

	def __str__(self):
		import inspect
		members = inspect.getmembers(standard_column_names, lambda a:not(inspect.isroutine(a)))
		
		members = [member for member in members if not member[0].startswith("__")]
		result = "Name used in code:"
		pad_length = max(max(len(member) for (member,value) in members),len(result))
		result = result.rjust(pad_length," ")+"   Output Column Name:\n"
		result += "-----".rjust(pad_length," ")+"   -----\n"
		for (member,value) in members:
			result += member.rjust(pad_length," ")+" : "+value+"\n"
		return result

class ExampleClass(metaclass=Printable_Class_Members):
		some_prop = "some_value"
		another_prop = "another_value"

class standard_column_names(metaclass=Printable_Class_Members):
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

	surface_width = "SurfWidth"
	surface_width_oldest = "SurfWidthOldest"
	surface_year = "SurfYr"
	surface_type = "SurfType"
	surface_aggregate_size = "Agg_Siz"
	surface_asphalt_type = "ASTP"

	corpex_speed_limit = "Spd_Lmt"
	corpex_rainfall = "Rain"
	corpex_average_temp = "TAve"
	corpex_minimum_temp = "TMin"
	corpex_link_category = "MABCD"
	corpex_aadt_year = "Traff_Yr"
	corpex_aadt = "AADT"

	curvature = "Curv"
	deflection = "Defl"
