import os

# bugger, we have to use oldstyle, htmlhelpcontroller is not in the new
# thunk layer yet
from wxPython.wx import *
import wxPython.html
from wxPython.htmlhelp import wxHtmlHelpController

class helpClass(object):
    def __init__(self, devideApp):
        wxFileSystem_AddHandler(wxZipFSHandler())        
        self._htmlHelpController = wxHtmlHelpController()
        
        helpDir = os.path.join(devideApp.getAppDir(), 'docs/help')
        mainBook = os.path.join(helpDir, 'devideHelp.htb')
        self._htmlHelpController.AddBook(mainBook, True)

    def close(self):
        self._htmlHelpController.Destroy()
        del self._htmlHelpController

    def show(self):
        self._htmlHelpController.DisplayContents()



        
        
