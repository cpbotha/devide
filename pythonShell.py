# python_interpreter.py copyright 2002 by Charl P. Botha http://cpbotha.net/
# $Id: pythonShell.py,v 1.6 2004/02/27 17:00:26 cpbotha Exp $
# window for interacting with the python interpreter during execution

from wxPython.wx import *
from wxPython.xrc import *
from wxPython import py # shell, version, filling

class pythonShell:

    def __init__(self, parentWindow, icon):
        self._parentWindow = parentWindow

        self._ps_frame = self._createFrame()

        # set icon
        self._ps_frame.SetIcon(icon)
        # make sure that when the window is closed, we just hide it (teehee)
        EVT_CLOSE(self._ps_frame, self.close_ps_frame_cb)

        EVT_BUTTON(self._ps_frame, self._ps_frame.closeButton.GetId(),
                   self.close_ps_frame_cb)

        # we can display ourselves
        self.show()

    def close(self):
        # take care of the frame
        if self._ps_frame:
            self._ps_frame.Destroy()
            del self._ps_frame

    def show(self):
        self._ps_frame.Show(True)
        self._ps_frame.Raise()

    def hide(self):
        self._ps_frame.Show(false)

    def close_ps_frame_cb(self, event):
        self.hide()

    def _createFrame(self):
        import resources.python.pythonShellFrame
        reload(resources.python.pythonShellFrame)
        
        frame = resources.python.pythonShellFrame.pythonShellFrame(
            self._parentWindow, id=-1, title="Dummy")

        return frame

    def injectLocals(self, localsDict):
        self._ps_frame.pyShell.interp.locals.update(localsDict)

    def setStatusBarMessage(self, message):
        self._ps_frame.statusBar.SetStatusText(message)


