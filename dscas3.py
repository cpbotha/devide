#!/usr/bin/env python
# $Id: dscas3.py,v 1.10 2003/01/19 23:13:37 cpbotha Exp $

import os
import stat
import sys

from assistants import assistants
from graph_editor import graph_editor
from module_manager import module_manager
from python_shell import python_shell
import gen_utils

from wxPython.wx import *
from wxPython.xrc import *

import vtk

# ---------------------------------------------------------------------------
class main_window(wxFrame):
    """Main dscas3 application window.

    This is class representing the main dscas3 window.  As is the convention
    with dscas3, the UI derivatives (like this window) will handle all UI
    and hand over to other code as soon as the transaction becomes UI
    independent.
    """

    def __init__(self, dscas3_app):
        # bind the app name so we can get to it for events
        self._dscas3_app = dscas3_app
        
        wxFrame.__init__(self, None, -1, "dscas3")

        # attempt to open the resource file
        res_path = os.path.join(sys.path[0], 'resources/xml/dscas3_main.xrc')
        # res is local, will go out of scope (and make wxXmlResource destruct)
        res = wxXmlResource(res_path)

        # get menubar from it
        menubar = res.LoadMenuBar('MBAR_MAIN_WINDOW')
        EVT_MENU(self, XMLID('ID_EXIT_MI'), self.exit_cb)
        EVT_MENU(self, XMLID('ID_GRAPH_EDITOR_MI'), self.graph_editor_cb)
        EVT_MENU(self, XMLID('ID_PYTHON_SHELL_MI'), self.python_shell_cb)
        # add the menubar to this frame
        self.SetMenuBar(menubar)
        
        # then get the panel out
        panel = res.LoadPanel(self, 'PNL_MAIN_WINDOW')

        # now make a status bar
        self.CreateStatusBar()
        self.GetStatusBar().SetStatusText('Welcome to DSCAS3.')
        self.GetStatusBar().SetMinHeight(10)

        # we do NOT add the status bar to the slicer, since it is mysteriously
        # added to the frame already, almost like the menubar
        top_sizer = wxBoxSizer(wxVERTICAL)
        top_sizer.Add(panel, option=1, flag=wxEXPAND)

        # make sure our frame makes use of the top level sizer
        self.SetAutoLayout(true)
        self.SetSizer(top_sizer)
        # resize our frame so it fits around the top level sizer (which
        # fits around the frame, which fits around its contained sizers, etc)
        top_sizer.Fit(self)
        # make sure the frame will have this as minimum size
        top_sizer.SetSizeHints(self)

        # get out status statictext and progress gauge so we can use these
        self._progress_stxt = XMLCTRL(self, 'ID_PROGRESS_STXT')
        self._progress_gauge = XMLCTRL(self, 'ID_PROGRESS_GAUGE')
        # set them up to some sane values
        self.set_progress(100, 'Started up.')

        # attach events to assistant buttons
        EVT_BUTTON(self, XMLID('ID_LOAD_DATA_BTN'), self.load_data_cb)

        # display ourselves
        self.Show(true)

    def set_progress(self, progress, message):
        self._progress_stxt.SetLabel(message)
        # you might want to use wxPyTypeCast on _progress_gauge, until the
        # OOR is done for wxGauge as well
        self._progress_gauge.SetValue(progress)
        wxYield()

    def exit_cb(self, event):
        self._dscas3_app.quit()

    def load_data_cb(self, event):
        self._dscas3_app.get_assistants().load_data()

    def graph_editor_cb(self, event):
        self._dscas3_app.start_graph_editor()

    def python_shell_cb(self, event):
        self._dscas3_app.start_python_shell()

# ---------------------------------------------------------------------------
class dscas3_log_window:
    """Log window that can display file or can be used as destination file
    object.

    If instantiated with a filename as parameter, one can regularly call
    update() for this class to check whether the filesize has changed since
    the last poll.  If the filesize has changed, it will display the contents
    in the text control.

    If instantiated without filename, this can be used as an output pipe,
    for instance to replace stdout and stderr with.  Neato.
    """
    
    def __init__(self, title, parent_frame=None, filename=None):
        self._filename = filename
        # get initial filesize so our update() polling thing works
        if self._filename:
            try:
                self._previous_fsize = os.stat(self._filename)[stat.ST_SIZE]
            except:
                # if we couldn't get it, just set it to -1
                # this means ANY new valid filesize will be different,
                # thus guaranteeing correct behaviour of update()
                self._previous_fsize = -1
            
        self._create_window(title, parent_frame)
        #

    def _create_window(self, title, parent_frame):
        self._view_frame = wxFrame(parent_frame, -1, title)
        EVT_CLOSE(self._view_frame, lambda e, s=self: s.hide())
        
        panel = wxPanel(self._view_frame, -1)
        self._textctrl = wxTextCtrl(panel, id=-1,
                                    size=wxSize(320,200),
                                    style=wxTE_MULTILINE | wxTE_READONLY)

        cid = wxNewId()
        cb = wxButton(panel, cid, 'Close')
        EVT_BUTTON(self._view_frame, cid, lambda e, s=self: s.hide())

        uid = wxNewId()
        ub = wxButton(panel, uid, 'Update')
        EVT_BUTTON(self._view_frame, uid, lambda e, s=self: s.update())
        
        button_sizer = wxBoxSizer(wxHORIZONTAL)
        button_sizer.Add(ub)
        button_sizer.Add(cb)

        tl_sizer = wxBoxSizer(wxVERTICAL)
        tl_sizer.Add(self._textctrl, option=1, flag=wxEXPAND)
        tl_sizer.Add(button_sizer, flag=wxALIGN_RIGHT)

        panel.SetAutoLayout(true)
        panel.SetSizer(tl_sizer)
        tl_sizer.Fit(self._view_frame)
        tl_sizer.SetSizeHints(self._view_frame)

    def show(self):
        self._view_frame.Show(true)

    def hide(self):
        self._view_frame.Show(false)

    def write(self, data):
        """Method so that we can be used as output pipe."""
        self._textctrl.write(data)
        self.show()

    def update(self):
        """Update textctrl contents according to self._filename, if this
        has been set.

        This should be called regularly, or whenever you know that the
        file it's watching could have changed.  If the file exists and the
        filesize has changed since the previous update, the textctrl will
        be cleared and the file will be read from scratch and contents will
        be put into the textctrl.
        """

        if self._filename:
            try:
                # if we can't get fsize, the file is borked, and we
                # should just leave it alone in anycase
                fsize = os.stat(self._filename)[stat.ST_SIZE]
                # first see if filesize has changed
                if not fsize == self._previous_fsize:
                    # try to open the log file
                    f = open(self._filename)
                    # put the contents in the text control
                    self._textctrl.SetValue(f.read())
                    # move the user to the last line
                    lp = self._textctrl.GetLastPosition()
                    self._textctrl.SetInsertionPoint(lp)
                    # now make sure this frame is visible
                    self.show()
                    # and update the previous size
                    self._previous_fsize = fsize
            except:
                # we let this go, silently
                pass
    
# ---------------------------------------------------------------------------
class dscas3_app_t(wxApp):
    """Main dscas3 application class.

    Class that's used as communication hub for most other components of the
    platform.  We've derived from wxApp but this is not a requirement... we
    could just as well have contained the wxApp instance.  This inheritance
    does not prevent abstraction from the GUI.
    """
    
    def __init__(self):
        self._old_stderr = None
        self._old_stdout = None
        
        self.main_window = None

        self._stdo_lw = None
        self._stde_lw = None
        self._vtk_lw = None

        #self._appdir, exe = os.path.split(sys.executable)
        if hasattr(sys, 'frozen') and sys.frozen:
            self._appdir, exe = os.path.split(sys.executable)
        else:
            dirname = os.path.dirname(sys.argv[0])
            if dirname and dirname != os.curdir:
                self._appdir = dirname
            else:
                self._appdir = os.getcwd()
        
        wxApp.__init__(self, 0)

        self._assistants = assistants(self)
        self._graph_editor = None
        self._python_shell = None
	
	# this will instantiate the module manager and get a list of plugins
	self.module_manager = module_manager(self)

    def OnInit(self):
        self.main_window = main_window(self)
        self.SetTopWindow(self.main_window)

        
        # after we get the gui going, we can redirect
        self._stde_lw = dscas3_log_window('Standard Error Log',
                                          self.main_window)
        self._old_stderr = sys.stderr
        #sys.stderr = self._stde_lw

        self._stdo_lw = dscas3_log_window('Standard Output Log',
                                          self.main_window)
        self._old_stdout = sys.stdout
        #sys.stdout = self._stdo_lw
        
        # now make sure that VTK will always send error to vtk.log logfile
        temp = vtk.vtkFileOutputWindow()
        vtk_logfn = os.path.join(self.get_appdir(), 'vtk.log')
        temp.SetFileName(vtk_logfn)
        #temp.SetInstance(temp)
        del temp

        self._vtk_lw = dscas3_log_window('VTK error log',
                                         self.main_window,
                                         vtk_logfn)
        
        return true

    def OnExit(self):
        sys.stderr = self._old_stderr
        sys.stdout = self._old_stdout
	
    def get_main_window(self):
        return self.main_window

    def get_module_manager(self):
	return self.module_manager

    def get_assistants(self):
        return self._assistants

    def get_appdir(self):
        return self._appdir
	
    def quit(self):
        # shutdown all modules gracefully
        self.module_manager.close()
	# take care of main window
	self.main_window.Close()

    def start_python_shell(self):
        if self._python_shell == None:
            self._python_shell = python_shell(self)
        else:
            self._python_shell.show()

    def start_graph_editor(self):
        if self._graph_editor == None:
            self._graph_editor = graph_editor(self)
        else:
            self._graph_editor.show()

    def update_vtk_log_window(self):
        self._vtk_lw.update()

    def set_progress(self, progress, message):
        self.main_window.set_progress(progress, message)
	
# ---------------------------------------------------------------------------


def main():
    dscas3_app = dscas3_app_t()
    dscas3_app.MainLoop()

if __name__ == '__main__':
    main()
    
