# $Id: __init__.py 1945 2006-03-05 01:06:37Z cpbotha $

# importing this module shouldn't directly cause other large imports
# do large imports in the init() hook so that you can call back to the
# moduleManager progress handler methods.

"""matplotlib_kit package driver file.

Inserts the following modules in sys.modules: pylab.

@author: Charl P. Botha <http://cpbotha.net/>
"""

import re
import sys
import types

# you have to define this
VERSION = 'SVN'

def init(theModuleManager):
    # import the main module itself
    import matplotlib
    matplotlib.use('WX')
    
    theModuleManager.setProgress(100, 'Initialising matplotlib_kit')

