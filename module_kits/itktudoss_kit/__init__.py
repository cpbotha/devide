# $Id: __init__.py 1945 2006-03-05 01:06:37Z cpbotha $

# importing this module shouldn't directly cause other large imports
# do large imports in the init() hook so that you can call back to the
# ModuleManager progress handler methods.

"""itktudoss_kit package driver file.

This driver makes sure that itktudoss has been integrated with the main WrapITK
instalation.

@author: Charl P. Botha <http://cpbotha.net/>
"""

import re
import sys
import types

# you have to define this
VERSION = 'SVN'

def init(theModuleManager, pre_import=True):
    theModuleManager.setProgress(80, 'Initialising itktudoss_kit: TPGAC')
    import itk # this will have been pre-imported by the itk_kit
    a = itk.TPGACLevelSetImageFilter
    theModuleManager.setProgress(100, 'Initialising itktudoss_kit: DONE')

