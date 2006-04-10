# $Id: __init__.py 1945 2006-03-05 01:06:37Z cpbotha $

# importing this module shouldn't directly cause other large imports
# do large imports in the init() hook so that you can call back to the
# moduleManager progress handler methods.

"""wxpython_kit package driver file.

Inserts the following modules in sys.modules: wx.

@author: Charl P. Botha <http://cpbotha.net/>
"""

# you have to define this
VERSION = ''

def init(theModuleManager):
    # import the main module itself
    global wx
    import wx

    import dvedit_window
    import dvshell

    # build up VERSION
    global VERSION
    VERSION = wx.VERSION_STRING

    theModuleManager.setProgress(100, 'Initialising wx_kit')
