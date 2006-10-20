# short DeVIDE matplotlib demo.

from pylab import *

# close previous figure if it exists
try:
    obj.mpl_close_figure(numpy_test_figure)
except NameError:
    pass

numpy_test_figure = obj.mpl_new_figure()

# this example from http://matplotlib.sourceforge.net/screenshots/log_shot.py
dt = 0.01
t = arange(dt, 20.0, dt)

subplot(211)
semilogx(t, sin(2*pi*t))
ylabel('semilog')
xticks([])
setp(gca(), 'xticklabels', [])
grid(True)

subplot(212)
loglog(t, 20*exp(-t/10.0), basey=4)
grid(True)
gca().xaxis.grid(True, which='minor')  # minor grid on too
xlabel('time (s)')
ylabel('loglog')
