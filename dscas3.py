#!/usr/bin/env python
# $Id: dscas3.py,v 1.3 2002/05/18 00:38:26 cpbotha Exp $

import os
import sys

from assistants import assistants
from graph_editor import graph_editor
from module_manager import module_manager
from python_shell import python_shell

from wxPython.wx import *
from wxPython.xrc import *


class main_window(wxFrame):
    """Main dscas3 application window.

    This is class representing the main dscas3 window.  As is the convention
    with dscas3, the UI derivatives (like this window) will handle all UI
    and hand over to other code as soon as the transaction becomes UI
    independent.
    """

    def __init__(self, dscas3_app):
        # bind the app name so we can get to it for events
        self.dscas3_app = dscas3_app
        
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
        self._status_stxt = XMLCTRL(self, 'ID_STATUS_STXT')
        self._progress_gauge = XMLCTRL(self, 'ID_PROGRESS_GAUGE')
        # set them up to some sane values
        self.set_status_message('Started up.')
        self.set_progress_gauge(100)

        # attach events to assistant buttons
        EVT_BUTTON(self, XMLID('ID_LOAD_DATA_BTN'), self.load_data_cb)

        # display ourselves
        self.Show(true)

    def set_status_message(self, message):
        self._status_stxt.SetLabel(message)

    def set_progress_gauge(self, progress):
        # you might want to use wxPyTypeCast on _progress_gauge, until the
        # OOR is done for wxGauge as well
        self._progress_gauge.SetValue(progress)
        pass

    def exit_cb(self, event):
        self.dscas3_app.quit()

    def load_data_cb(self, event):
        self.dscas3_app.get_assistants().load_data()

    def graph_editor_cb(self, event):
        self.dscas3_app.start_graph_editor()

    def python_shell_cb(self, event):
        self.dscas3_app.start_python_shell()

class wx_output_pipe:
    def write(self, data):
        print "SOMETHING ELSE! %s" % (data)
        
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
        
        wxApp.__init__(self, 0)

        self._assistants = assistants(self)
        self._graph_editor = None
        self._python_shell = None
	
	# this will instantiate the module manager and get a list of plugins
	self.module_manager = module_manager(self)

    def OnInit(self):
        self.main_window = main_window(self)
        self.SetTopWindow(self.main_window)

        # after we have the gui going, we can redirect
        _output_pipe = wx_output_pipe()
        self._old_stderr = sys.stderr
        sys.stderr = _output_pipe
#        self._old_stdout = sys.stdout
#        sys.stdout = _output_pipe
        
        # "true" is defined in wxPython.wx
        return true

    def OnExit(self):
        sys.stderr = self._old_stderr
#        sys.stdout = self._old_stdout
#        return true
	
    def get_main_window(self):
        return self.main_window

    def get_module_manager(self):
	return self.module_manager

    def get_assistants(self):
        return self._assistants
	
    def quit(self):
	print "quit called!"
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
	

def main():
    dscas3_app = dscas3_app_t()
    dscas3_app.MainLoop()

if __name__ == '__main__':
    main()
    
