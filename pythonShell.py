# python_interpreter.py copyright 2002 by Charl P. Botha http://cpbotha.net/
# $Id: pythonShell.py,v 1.7 2004/03/22 21:57:38 cpbotha Exp $
# window for interacting with the python interpreter during execution

from wxPython.wx import *
from wxPython.xrc import *
from wxPython import py # shell, version, filling

class pythonShell:

    def __init__(self, parentWindow, icon):
        self._parentWindow = parentWindow

        self._psFrame = self._createFrame()

        # set icon
        self._psFrame.SetIcon(icon)
        # make sure that when the window is closed, we just hide it (teehee)
        EVT_CLOSE(self._psFrame, self.close_ps_frame_cb)

        EVT_BUTTON(self._psFrame, self._psFrame.closeButton.GetId(),
                   self.close_ps_frame_cb)

        # we can display ourselves
        self.show()

    def close(self):
        # take care of the frame
        if self._psFrame:
            self._psFrame.Destroy()
            del self._psFrame

    def show(self):
        self._psFrame.Show(True)
        self._psFrame.Raise()

    def hide(self):
        self._psFrame.Show(false)

    def close_ps_frame_cb(self, event):
        self.hide()

    def _createFrame(self):
        import resources.python.pythonShellFrame
        reload(resources.python.pythonShellFrame)
        
        frame = resources.python.pythonShellFrame.pythonShellFrame(
            self._parentWindow, id=-1, title="Dummy")

        return frame

    def injectLocals(self, localsDict):
        self._psFrame.pyShell.interp.locals.update(localsDict)

    def setStatusBarMessage(self, message):
        self._psFrame.statusBar.SetStatusText(message)


