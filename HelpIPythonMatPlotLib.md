# ipython #

Make sure you start ipython with:
```
dre ipython -pylab
```

Now you can pylab away:
```
a = arange(-pi, pi, 0.01)
plot(a, sin(a))
grid()
```

# ipythonwx #

Slightly more involved.  Start ipythonwx up with:
```
dre ipythonwx
```
... then make sure that the "Execute in thread" checkbox at the bottom of the ipythonwx is UNCHECKED.  If you don't do this, things will crash.

Type the following before you start:
```
import matplotlib
matplotlib.interactive(True)
from pylab import *
```
(the first two lines will not be necessary in future (after 9.8) releases of the DRE.)

... and pylab away:
```
a = arange(-pi, pi, 0.01)
plot(a, sin(a))
grid()
```