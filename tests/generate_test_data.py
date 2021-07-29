
import pandas as pd
import numpy as np
import numpy.ma as ma
import dtimsprep.merge as merge



roads = numpy.array([
	"H001",
	"H002",
	"H003",
	"H004",
	"H005",
	"M001",
	"M002",
	"M003",
	"M004",
])

roads.shuffle()

cwys = [
	"L",
	"S",
	"R"
]

slk_min = 0
slk_max = 1000

result = []

for road in roads:
	for cwy in cwys:

		# generate some random steps between 10 meters and 5000 km, rounded to the nearest 10 meters
		(np.random_integers(1, 500, shape=(1,2000))*10).
		mask = np.random_integers(100, shape=(1,2000))>99)
		steps = mp.masked_array(
			np.random_integers(1, 500, shape=(1,2000))*10),
			mask = np.random_integers(100, shape=(1,2000))>99)
		seg_start = slk_min
		
		
