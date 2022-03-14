import pandas as pd
import numpy as np
import dtimsprep.merge as merge


def test_IndexOfMax():

	segments = pd.DataFrame(
		columns=["road", "cwy", "slk_from", "slk_to"],
		data=[
			["H001", "L",   0, 100],
			["H001", "L", 100, 200],
			["H001", "L", 200, 300],
			["H001", "L", 300, 400],
			["H001", "L", 400, 500],
		]
	)

	data = pd.DataFrame(
		columns=["road", "cwy", "slk_from", "slk_to", "measure", "category"],
		data=[
			["H001", "L",  50, 140, 1.0, "A"],  # 50 40   0  0
			["H001", "L", 140, 160, 2.0, "B"],  # 0  20   0  0
			["H001", "L", 160, 180, 3.0, "C"],  # 0  20   0  0
			["H001", "L", 180, 220, 4.0, "D"],  # 0  20  20  0
			["H001", "L", 220, 240, 5.0, "E"],  # 0   0  20  0
			["H001", "L", 240, 260, 5.0, "F"],  # 0   0  20  0
			["H001", "L", 260, 280, 6.0, "G"],  # 0   0  20  0
			["H001", "L", 280, 290, 7.0, "H"],  # 0   0  10  0
			["H001", "L", 290, 320, 8.0, "I"],  # 0   0  10 20
		]
	)

	data = data.set_index("category")

	expected_output = pd.DataFrame(
		columns=["road", "cwy", "slk_from", "slk_to", "argmax"],
		data=[
			["H001", "L",   0, 100, "A"],
			["H001", "L", 100, 200, "D"],
			["H001", "L", 200, 300, "I"],
			["H001", "L", 300, 400, "I"],
			["H001", "L", 400, 500, np.nan],
		]
	)

	res = merge.on_slk_intervals(
		segments,
		data,
		["road", "cwy"],
		[
			merge.Action('measure', aggregation=merge.Aggregation.IndexOfMax(), rename="argmax"),
		],
		from_to=("slk_from", "slk_to"),
	)
	
	assert res.compare(expected_output).empty