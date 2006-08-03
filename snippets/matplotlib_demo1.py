# short DeVIDE matplotlib demo.

from pylab import *

# close previous figure if it exists
try:
    obj.mpl_close_figure(numpy_test_figure)
except NameError:
    pass

numpy_test_figure = obj.mpl_new_figure()

a = arange(-30, 30, 0.01)
plot(a, sin(a) / a, label='sinc(x)')
plot(a, cos(a), label='cos(x)')
legend()
grid()

xlabel('x')
ylabel('f(x)')

