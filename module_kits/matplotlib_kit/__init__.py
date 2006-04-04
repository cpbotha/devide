# $Id: __init__.py 1945 2006-03-05 01:06:37Z cpbotha $

# importing this module shouldn't directly cause other large imports
# do large imports in the init() hook so that you can call back to the
# moduleManager progress handler methods.

# NB: to get this packaged up with numpy 0.9.6, you have to apply the
# patch at http://projects.scipy.org/scipy/numpy/changeset/2304
# so that the scipy-style subpackages are loaded with imports

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

    # these are also needed with numpy 0.9.6 to get all deps in here
    import numpy.lib
    import numpy.core
    import numpy.core._internal

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

    

