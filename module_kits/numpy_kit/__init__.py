# $Id: __init__.py 1945 2006-03-05 01:06:37Z cpbotha $

# importing this module shouldn't directly cause other large imports
# do large imports in the init() hook so that you can call back to the
# ModuleManager progress handler methods.

"""numpy_kit package driver file.

Inserts the following modules in sys.modules: numpy.

@author: Charl P. Botha <http://cpbotha.net/>
"""

import os
import re
import sys
import types

# you have to define this
VERSION = ''

def init(theModuleManager, pre_import=True):
    theModuleManager.setProgress(5, 'Initialising numpy_kit: start')

    # import numpy into the global namespace
    global numpy
    import numpy

    # we add this so that modules using "import Numeric" will probably also
    # work (such as the FloatCanvas)
    sys.modules['Numeric'] = numpy
    sys.modules['numarray'] = numpy

    theModuleManager.setProgress(95, 'Initialising numpy_kit: import done')

    # build up VERSION
    global VERSION
    VERSION = '%s' % (numpy.version.version,)

    theModuleManager.setProgress(100, 'Initialising numpy_kit: complete')

    

