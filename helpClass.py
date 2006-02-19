import os

# bugger, we have to use oldstyle, htmlhelpcontroller is not in the new
# thunk layer yet
#from wxPython.wx import *
#import wxPython.html
#from wxPython.htmlhelp import wxHtmlHelpController

import wx
import wx.html

class helpClass(object):
    def __init__(self, app_dir):
        wx.FileSystem_AddHandler(wx.ZipFSHandler())
        self._htmlHelpController = wx.html.HtmlHelpController()
        
        helpDir = os.path.join(app_dir, 'docs/help')
        mainBook = os.path.join(helpDir, 'devideHelp.htb')
        self._htmlHelpController.AddBook(mainBook, True)

    def close(self):
        # Robin says that in this case, a Destroy() is not necessary
        # Destroy() segfaulted on wxPython 2.6.0.1, Robin is fixing that
        del self._htmlHelpController

    def show(self):
        self._htmlHelpController.DisplayContents()



        
        
