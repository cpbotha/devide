# $Id: __init__.py 1945 2006-03-05 01:06:37Z cpbotha $

# importing this module shouldn't directly cause other large imports
# do large imports in the init() hook so that you can call back to the
# moduleManager progress handler methods.

"""itktud_kit package driver file.

This driver makes sure that itktud has been integrated with the main WrapITK
instalation.

@author: Charl P. Botha <http://cpbotha.net/>
"""

import re
import sys
import types

# you have to define this
VERSION = 'SVN'

def init(theModuleManager):
    theModuleManager.setProgress(80, 'Initialising itktud_kit: TPGAC')
    import itk # this will have been pre-imported by the itk_kit
    a = itk.TPGACLevelSetImageFilter
    theModuleManager.setProgress(100, 'Initialising itktud_kit: DONE')

