# short DeVIDE matplotlib demo.

from pylab import *

# close previous figure if it exists
try:
    obj.mpl_close_figure(numpy_test_figure)
except NameError:
    pass

# square figure and square axes looks better for polar plots
numpy_test_figure = obj.mpl_new_figure(figsize=(8,8))
ax = axes([0.1, 0.1, 0.8, 0.8], polar=True, axisbg='#d5de9c')

# following example from http://matplotlib.sourceforge.net/screenshots/polar_demo.py

# radar green, solid grid lines
rc('grid', color='#316931', linewidth=1, linestyle='-')
rc('xtick', labelsize=15)
rc('ytick', labelsize=15)

r = arange(0,1,0.001)
theta = 2*2*pi*r
polar(theta, r, color='#ee8d18', lw=3)

setp(ax.thetagridlabels, y=1.075) # the radius of the grid labels

title("And there was much rejoicing!", fontsize=20)
