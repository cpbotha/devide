# $Id: __init__.py 1945 2006-03-05 01:06:37Z cpbotha $

# importing this module shouldn't directly cause other large imports
# do large imports in the init() hook so that you can call back to the
# moduleManager progress handler methods.

"""matplotlib_kit package driver file.

Inserts the following modules in sys.modules: matplotlib, pylab.

@author: Charl P. Botha <http://cpbotha.net/>
"""

import re
import sys
import types

# you have to define this
VERSION = ''

def init(theModuleManager):
    # import the main module itself
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

    global numpy
    import numpy

    theModuleManager.setProgress(40, 'Initialising matplotlib_kit: numpy')

    # import the pylab interface, make sure it's available from this namespace
    global pylab
    import pylab
    
    theModuleManager.setProgress(90, 'Initialising matplotlib_kit: pylab')

    # build up VERSION
    global VERSION
    VERSION = '%s (numpy %s matplotlib %s)' % ('SVN', numpy.version.version,
                                               matplotlib.__version__)

    theModuleManager.setProgress(100, 'Initialising matplotlib_kit: complete')

    

