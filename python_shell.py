# python_interpreter.py copyright 2002 by Charl P. Botha http://cpbotha.net/
# $Id: python_shell.py,v 1.8 2003/10/06 22:13:42 cpbotha Exp $
# window for interacting with the python interpreter during execution

from wxPython.wx import *
from wxPython.xrc import *
from wxPython import py # shell, version, filling

class python_shell:

    def __init__(self, app):
        self._app = app

        # main frame
        self._ps_frame = wxFrame(parent=self._app.get_main_window(), id=-1,
                                 title="Python Interpreter (PyCrust)")
        # set icon
        self._ps_frame.SetIcon(self._app.getApplicationIcon())
        # make sure that when the window is closed, we just hide it (teehee)
        EVT_CLOSE(self._ps_frame, self.close_ps_frame_cb)
        
        panel = wxPanel(parent=self._ps_frame, id=-1)

        # create splitter window for the shell and filling to go in
        split_win = wxSplitterWindow(parent=panel, id=-1,
                                     size=(640,480))
        # initialise shell window (derived from wxStyledTextCtrl)
        # create locals dictionary with only the application instance in it
        print dir(py.shell)
        shell_win = py.shell.Shell(parent=split_win,
                                   locals={'dscas3_app' : self._app})
        # and the filling of course (derived from wxSplitterWindow)
        # make it use the same root namespace is the shell
        filling_win = py.filling.Filling(parent=split_win,
                                      rootObject=shell_win.interp.locals,
                                      rootIsNamespace=1,
                                      size=(640,480))
        # now split the split window
        split_win.SplitHorizontally(shell_win, filling_win)


        # and we're going to use a sizer so that our buttons at the bottom
        # stay intact
        top_sizer = wxBoxSizer(wxVERTICAL)
        top_sizer.Add(split_win, option=1, flag=wxEXPAND)
        close_id = wxNewId()
        top_sizer.Add(wxButton(parent=panel, id=close_id,
                               label="Close"),
                      option=0, flag=wxALIGN_RIGHT)
        EVT_BUTTON(self._ps_frame, close_id, self.close_ps_frame_cb)

        # panel.Layout will be called automatically during resizes
        panel.SetAutoLayout(True)
        # panel will now own the sizer; also, panel.Layout() will use the sizer
        panel.SetSizer(top_sizer)
        # resize the frame to fit around the sizer; the sizer automatically
        # fits around the controls that have been added to it
        top_sizer.Fit(self._ps_frame)
        # set minimal size of the frame to be minimal size of the sizer
        top_sizer.SetSizeHints(self._ps_frame)
        # hmmm, it seems the wxPanel is linked to the wxFrame; if the wxFrame
        # gets resized, the wxPanel does too
        

        # we can display ourselves
        self.show()

    def close(self):
        # take care of the frame
        if self._ps_frame:
            self._ps_frame.Destroy()
            del self._ps_frame

    def show(self):
        self._ps_frame.Show(True)

    def hide(self):
        self._ps_frame.Show(false)

    def close_ps_frame_cb(self, event):
        self.hide()
        

