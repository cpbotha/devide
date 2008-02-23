# $Id: __init__.py 1945 2006-03-05 01:06:37Z cpbotha $

# importing this module shouldn't directly cause other large imports
# do large imports in the init() hook so that you can call back to the
# moduleManager progress handler methods.

"""matplotlib_kit package driver file.

Inserts the following modules in sys.modules: matplotlib, pylab.

@author: Charl P. Botha <http://cpbotha.net/>
"""

import os
import re
import sys
import types

# you have to define this
VERSION = ''

def init(theModuleManager):

    if hasattr(sys, 'frozen') and sys.frozen:
        # matplotlib supports py2exe by checking for matplotlibdata in the appdir
        # but this is only done on windows (and therefore works for our windows
        # installer builds).  On non-windows, we have to stick it in the env
        # to make sure that MPL finds its datadir (only if we're frozen)
        mpldir = os.path.join(theModuleManager.get_appdir(), 'matplotlibdata')
        os.environ['MATPLOTLIBDATA'] = mpldir

    
    # import the main module itself
    # this doesn't import numerix yet...
    global matplotlib
    import matplotlib

    # use WX + Agg backend (slower, but nicer that WX)
    matplotlib.use('WXAgg')
    # interactive mode: user can use pylab commands from any introspection
    # interface, changes will be made immediately and matplotlib cooperates
    # nicely with main WX event loop
    matplotlib.interactive(True)
    # makes sure we use the numpy backend
    from matplotlib import rcParams
    rcParams['numerix'] = 'numpy'

    theModuleManager.setProgress(25, 'Initialising matplotlib_kit: config')

    # @PATCH:
    # this is for the combination numpy 1.0.4 and matplotlib 0.91.2
    # matplotlib/numerix/ma/__init__.py:
    # . normal installation fails on "from numpy.ma import *", so "from
    #   numpy.core.ma import *" is done, thus bringing in e.g. getmask
    # . pyinstaller binaries for some or other reason succeed on 
    #   "from numpy.ma import *" (no exception raised), therefore do
    #   not do "from numpy.core.ma import *", and therefore things like
    #   getmask are not imported.
    # solution:
    # we make sure that "from numpy.ma import *" actually brings in
    # numpy.core.ma by importing that and associating the module
    # binding to the global numpy.ma.
    if hasattr(sys, 'frozen') and sys.frozen:
        import numpy.core.ma
        sys.modules['numpy.ma'] = sys.modules['numpy.core.ma']

    # import the pylab interface, make sure it's available from this namespace
    global pylab
    import pylab

    theModuleManager.setProgress(90, 'Initialising matplotlib_kit: pylab')

    # build up VERSION
    global VERSION
    VERSION = '%s' % (matplotlib.__version__,)

    theModuleManager.setProgress(100, 'Initialising matplotlib_kit: complete')

    

