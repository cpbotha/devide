import os

# on windows, use win32help to show the chm file
# on anything else, show the crappy htb file.

# helpClass should be somewhere in the wx_interface.  think about
# that!

try:
    import win32help
    help_type = 0
except ImportError:
    import wx
    import wx.html
    help_type = 1

class helpClass(object):
    def __init__(self, devide_app):
        app_dir = devide_app.get_appdir()
        helpDir = os.path.join(app_dir, 'docs/help')
       
        if help_type > 0:
            wx.FileSystem_AddHandler(wx.ZipFSHandler())
            self._htmlHelpController = wx.html.HtmlHelpController()
       
            self._help_file = os.path.join(helpDir, 'devide.htb')
            self._htmlHelpController.AddBook(self._help_file, True)

        else:
            self._help_file = os.path.join(helpDir, 'devide.chm')
            self._frame = devide_app.get_interface()._main_frame

    def close(self):
        # Robin says that in this case, a Destroy() is not necessary
        # Destroy() segfaulted on wxPython 2.6.0.1, Robin is fixing that
        if help_type > 0:
            del self._htmlHelpController

    def show(self):
        if help_type > 0:
            self._htmlHelpController.DisplayContents()
        else:
            win32help.HtmlHelp(self._frame.GetHandle(),
                    self._help_file, win32help.HH_DISPLAY_TOPIC,
                    'introduction.html')




        
        
