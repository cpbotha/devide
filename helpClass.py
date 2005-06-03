import os

# bugger, we have to use oldstyle, htmlhelpcontroller is not in the new
# thunk layer yet
#from wxPython.wx import *
#import wxPython.html
#from wxPython.htmlhelp import wxHtmlHelpController

import wx
import wx.html

class helpClass(object):
    def __init__(self, devideApp):
        wx.FileSystem_AddHandler(wx.ZipFSHandler())
        self._htmlHelpController = wx.html.HtmlHelpController()
        
        helpDir = os.path.join(devideApp.getAppDir(), 'docs/help')
        mainBook = os.path.join(helpDir, 'devideHelp.htb')
        self._htmlHelpController.AddBook(mainBook, True)

    def close(self):
        self._htmlHelpController.Destroy()
        del self._htmlHelpController

    def show(self):
        self._htmlHelpController.DisplayContents()



        
        
