# python_interpreter.py copyright 2002 by Charl P. Botha http://cpbotha.net/
# $Id: python_shell.py,v 1.1 2002/04/23 14:09:29 cpbotha Exp $
# window for interacting with the python interpreter during execution

from wxPython.wx import *
from wxPython.xrc import *
from wxPython.lib.PyCrust import shell, version, filling

class python_shell:

    def __init__(self, app):
        self._app = app

        # main frame
        self._ps_frame = wxFrame(parent=self._app.get_main_window(), id=-1,
                                 title="Python Interpreter (PyCrust)")
        # make sure that when the window is closed, we just hide it (teehee)
        EVT_CLOSE(self._ps_frame, self.close_ps_frame_cb)

        # create splitter window for the shell and filling to go in
        split_win = wxSplitterWindow(parent=self._ps_frame, id=-1,
                                     size=(640,480))
        # initialise shell window (derived from wxStyledTextCtrl)
        # create locals dictionary with only the application instance in it
        shell_win = shell.Shell(parent=split_win,
                                locals={'dscas3_app' : self._app})
        # and the filling of course (derived from wxSplitterWindow)
        # make it use the same root namespace is the shell
        filling_win = filling.Filling(parent=split_win,
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
        top_sizer.Add(wxButton(parent=self._ps_frame, id=close_id,
                               label="Close"),
                      option=0, flag=wxALIGN_RIGHT)
        EVT_BUTTON(self._ps_frame, close_id, self.close_ps_frame_cb)
        # make sure the frame uses the sizer
        self._ps_frame.SetAutoLayout(true)
        self._ps_frame.SetSizer(top_sizer)
        # fit the frame around the sizer
        top_sizer.Fit(self._ps_frame)
        top_sizer.SetSizeHints(self._ps_frame)

        # we can display ourselves
        self.show()

    def __del__(self):
        # take care of the frame
        if self._ps_frame:
            self._ps_frame.Destroy()
            del self._ps_frame
        # unbind the resource
        del self._res

    def show(self):
        self._ps_frame.Show(true)

    def hide(self):
        self._ps_frame.Show(false)

    def close_ps_frame_cb(self, event):
        self.hide()
        

