# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

# importing this module shouldn't directly cause other large imports
# do large imports in the init() hook so that you can call back to the
# ModuleManager progress handler methods.

"""wxpython_kit package driver file.

Inserts the following modules in sys.modules: wx.

@author: Charl P. Botha <http://cpbotha.net/>
"""

# you have to define this
VERSION = ''


def init(theModuleManager, pre_import=True):
    # import the main module itself
    global wx
    import wx

    from . import dvedit_window
    from . import dvshell
    from . import python_shell_mixin
    from . import python_shell
    from . import utils

    # build up VERSION
    global VERSION
    VERSION = wx.VERSION_STRING

    theModuleManager.setProgress(100, 'Initialising wx_kit')
