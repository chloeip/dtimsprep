import numpy as np
import pandas as pd
from dtimsprep import merge as merge
from matplotlib import pyplot as plt
from matplotlib.ticker import MultipleLocator, AutoMinorLocator


class cn:
	road = "road"
	slk_from = "slk_from"
	slk_to = "slk_to"
	value = "value"


def plot_dist(ax: plt.Axes, df, title=None, height=None):
	if height is None:
		draw_heights = [20 for item in df.index]
	else:
		draw_heights = height
	
	if title is not None:
		ax.set_title(title)
	
	ax.set_axisbelow(True)
	ax.grid(
		True,
		which='minor',
		axis='both',
		color="#CCCCCC",
		linestyle='dotted'
	)
	ax.grid(
		True,
		which='major',
		axis='both'
	)
	ax.xaxis.set_major_locator(MultipleLocator(10))
	ax.xaxis.set_minor_locator(AutoMinorLocator(5))
	
	ax.yaxis.set_major_locator(MultipleLocator(100))
	ax.yaxis.set_minor_locator(AutoMinorLocator(2))
	
	ax.set_ymargin(0.1)
	
	ax.xaxis.set_tick_params('both', True)
	
	ax.bar(
		x=df[cn.slk_from],
		height=draw_heights,
		width=df[cn.slk_to] - df[cn.slk_from],
		align='edge',
		linewidth=1,
		edgecolor='black',
		alpha=0.6
	)
	if height is not None:
		for patch, draw_height in zip(ax.patches, draw_heights):
			ax.text(
				patch.get_x() + patch.get_width() / 2,
				patch.get_y() + patch.get_height(),
				np.nan if np.isnan(draw_height) else str(round(draw_height * 100) / 100),
				va="bottom",
				ha="center",
				fontdict={"size": 8}
			)


def test_pytest():
	assert True


def test_plot_1():
	seg = pd.DataFrame([
		[1, 10, 20],
		[1, 20, 50],
		[1, 50, 100]
	], columns=[cn.road, cn.slk_from, cn.slk_to])
	
	dat = pd.DataFrame([
		[1, 0, 15, 500],
		[1, 15, 30, 600],
		[1, 30, 40, 450],
		[1, 40, 45, 420],
		[1, 45, 60, 400],
		[1, 60, 80, 600],
		[1, 80, 85, 540],
		[1, 90, 105, 470],
	], columns=[cn.road, cn.slk_from, cn.slk_to, cn.value])
	
	plot_seg_vs_merged(seg, dat)


def test_plot_2():
	seg = pd.DataFrame([
		[1, 10, 20],
		[1, 20, 30],
		[1, 30, 40],
		[1, 40, 50],
		[1, 50, 60],
		[1, 60, 70],
		[1, 70, 80],
		[1, 80, 90],
		[1, 90, 100],
		[1, 100, 110],
		[1, 110, 120]
	], columns=[cn.road, cn.slk_from, cn.slk_to])
	
	dat = pd.DataFrame([
		[1, 0, 15, 500],
		[1, 15, 30, 600],
		[1, 30, 40, 450],
		[1, 40, 45, 420],
		[1, 45, 60, 400],
		[1, 60, 80, 600],
		[1, 80, 85, 540],
		[1, 90, 105, 470],
	], columns=[cn.road, cn.slk_from, cn.slk_to, cn.value])
	
	plot_seg_vs_merged(seg, dat)


def plot_seg_vs_merged(seg, dat):
	mer = merge.on_slk_intervals(
		target=seg,
		data=dat,
		join_left=[cn.road],
		column_actions=[
			merge.Action(cn.value, merge.Aggregation.KeepLongest(), rename="longest"),
			merge.Action(cn.value, merge.Aggregation.LengthWeightedAverage(), rename="l w average"),
			merge.Action(cn.value, merge.Aggregation.LengthWeightedPercentile(0.75), rename="75th percentile"),
			merge.Action(cn.value, merge.Aggregation.LengthWeightedPercentile(0.5), rename="50th percentile"),
			merge.Action(cn.value, merge.Aggregation.Average(), rename="Average")
		]
	)
	
	fig, axs = plt.subplots(2, 3, sharex='all', sharey='all')
	plot_dist(axs[0, 0], dat, title="Original", height=dat[cn.value])
	plot_dist(axs[0, 1], mer, title="Keep Longest", height=mer["longest"])
	plot_dist(axs[0, 2], mer, title="Length Weighted Average", height=mer["l w average"])
	plot_dist(axs[1, 0], mer, title="75th Percentile", height=mer["75th percentile"])
	plot_dist(axs[1, 1], mer, title="50th Percentile", height=mer["50th percentile"])
	plot_dist(axs[1, 2], mer, title="Average", height=mer["Average"])
	plt.tight_layout()
	plt.show()
