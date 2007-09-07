# $Id: __init__.py 1945 2006-03-05 01:06:37Z cpbotha $

# importing this module shouldn't directly cause other large imports
# do large imports in the init() hook so that you can call back to the
# moduleManager progress handler methods.

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

def init(theModuleManager):
    theModuleManager.setProgress(5, 'Initialising numpy_kit: start')

    # we add the path of this kit and of its numpy subdir so that
    # the frozen/installed version can import it
    # with the new pyinstaller 1.3, it IMPORTANT to add this to the
    # beginning of the sys.path, as on systems where Python is
    # installed, this somehow also gets added to the sys.path and then
    # parts of the system numpy are important!!
    p1 = os.path.dirname(__file__)
    p2 = os.path.join(p1, 'numpy')
    sys.path.insert(0, p1)
    sys.path.insert(0, p2)

    # after this, 'numpy' exists within our namespace, and
    # sys.modules['numpy'] contains a ref to our import (although it might
    # still have the default path c:\python24\lib\site-packages\numpy)
    global numpy
    import numpy

    # we add this so that modules using "import Numeric" will probably also
    # work (such as the FloatCanvas)
    sys.modules['Numeric'] = numpy
    sys.modules['numarray'] = numpy

    # remove the two paths that we inserted so we don't confuse anybody
    # with relative package imports that act strangely
    # remove from beginning of path
    del sys.path[0]
    del sys.path[0]

    theModuleManager.setProgress(95, 'Initialising numpy_kit: import done')

    # build up VERSION
    global VERSION
    VERSION = '%s' % (numpy.version.version,)

    theModuleManager.setProgress(100, 'Initialising numpy_kit: complete')

    

