# python_interpreter.py copyright 2002 by Charl P. Botha http://cpbotha.net/
# $Id: pythonShell.py,v 1.13 2004/06/23 11:51:32 cpbotha Exp $
# window for interacting with the python interpreter during execution

import os
import wx

class pythonShell:

    def __init__(self, parentWindow, devideApp):
        self._parentWindow = parentWindow

        self._psFrame = self._createFrame()

        # set icon
        icon = devideApp.getApplicationIcon()
        self._psFrame.SetIcon(icon)
        # make sure that when the window is closed, we just hide it (teehee)
        wx.EVT_CLOSE(self._psFrame, self.close_ps_frame_cb)

        wx.EVT_BUTTON(self._psFrame, self._psFrame.closeButton.GetId(),
                      self.close_ps_frame_cb)

        # we always start in this directory with our fileopen dialog
        self._snippetsDir = os.path.join(devideApp.getAppDir(), 'snippets')
        wx.EVT_BUTTON(self._psFrame, self._psFrame.loadSnippetButton.GetId(),
                      self._handlerLoadSnippet)

        # we can display ourselves
        self.show()

    def close(self):
        # take care of the frame
        if self._psFrame:
            self._psFrame.Destroy()
            del self._psFrame

    def show(self):
        self._psFrame.Show(True)
        self._psFrame.Iconize(False)        
        self._psFrame.Raise()

    def hide(self):
        self._psFrame.Show(False)

    def close_ps_frame_cb(self, event):
        self.hide()

    def _createFrame(self):
        import resources.python.pythonShellFrame
        reload(resources.python.pythonShellFrame)
        
        frame = resources.python.pythonShellFrame.pythonShellFrame(
            self._parentWindow, id=-1, title="Dummy")

        return frame

    def _handlerLoadSnippet(self, event):
        dlg = wx.FileDialog(self._psFrame, 'Choose a Python snippet to load.',
                            self._snippetsDir, '',
                            'Python files (*.py)|*.py|All files (*.*)|*.*',
                            wx.OPEN)

        if dlg.ShowModal() == wx.ID_OK:
            # get the path
            path = dlg.GetPath()
            # store the dir in the self._snippetsDir
            self._snippetsDir = os.path.dirname(path)
            # actually run the snippet
            self.loadSnippet(path)

        # take care of the dlg
        dlg.Destroy()

    def injectLocals(self, localsDict):
        self._psFrame.pyShell.interp.locals.update(localsDict)

    def loadSnippet(self, path):
        try:
            # redirect std thingies so that output appears in the shell win
            self._psFrame.pyShell.redirectStdout()
            self._psFrame.pyShell.redirectStderr()
            self._psFrame.pyShell.redirectStdin()

            # runfile also generates an IOError if it can't load the file
            execfile(path, globals(), self._psFrame.pyShell.interp.locals)

            
        except IOError,e:
            md = wx.MessageDialog(
                self._psFrame,
                'Could not open file %s: %s' % (path, str(e)), 'Error',
                wx.OK|wx.ICON_ERROR)
            md.ShowModal()

        # whatever happens, advance shell window with one line so
        # the user can type again
        self._psFrame.pyShell.push('')

        # redirect thingies back
        self._psFrame.pyShell.redirectStdout(False)
        self._psFrame.pyShell.redirectStderr(False)
        self._psFrame.pyShell.redirectStdin(False)
        

    def setStatusBarMessage(self, message):
        self._psFrame.statusBar.SetStatusText(message)


