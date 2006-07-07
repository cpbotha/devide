# python_interpreter.py copyright 2002 by Charl P. Botha http://cpbotha.net/
# $Id$
# window for interacting with the python interpreter during execution

import os
import module_kits.wx_kit
from module_kits.wx_kit.python_shell_mixin import PythonShellMixin
import wx

class Tab:
    def __init__(self, editwindow, interp):
        self.editwindow = editwindow
        self.editwindow.set_interp(interp)
        self.filename = ''
        self.modified = False

    def close(self):
        del self.editwindow

class Tabs:
    def __init__(self, notebook, parent_window):
        
        self.notebook = notebook
        self.parent_window = parent_window
        self.tab_list = []

    def add_existing(self, editwindow, interp):
        self.tab_list.append(Tab(editwindow, interp))
        self.set_observer_modified(-1)
        editwindow.SetFocus()

    def can_close(self, idx):
        """Check if current edit can be closed, also taking action if user
        would like to save data first.

        @return: True if edit is unmodified OR user has indicated that the
        edit can be closed.
        """

        if not self.tab_list[idx].modified:
            return True

        md = wx.MessageDialog(
            self.parent_window,
            "Current edit has not been saved.  "
            "Are you sure you want to close it?", "Close confirmation", 
            style = wx.YES_NO | wx.ICON_QUESTION)

        if md.ShowModal() == wx.ID_YES:
            return True

        else:
            return False
        

    def close_current(self):
        if self.notebook.GetPageCount() < 2:
            wx.LogWarning('You can not close the last remaining tab.')
            wx.Log_FlushActive()

        else:
            sel = self.notebook.GetSelection()
            if sel >= 0:
                if self.can_close(sel):
                    self.notebook.DeletePage(sel)
                    del self.tab_list[sel]

    def create_new(self, interp):
        pane = wx.Panel(self.notebook, -1)
        editwindow = module_kits.wx_kit.dvedit_window.DVEditWindow(pane, -1)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(editwindow, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 7)

        pane.SetAutoLayout(True)
        pane.SetSizer(sizer)
        sizer.Fit(pane)
        sizer.SetSizeHints(pane)

        self.notebook.AddPage(pane, "Unnamed")
        self.notebook.SetSelection(self.notebook.GetPageCount() - 1)
        editwindow.SetFocus()

        self.tab_list.append(Tab(editwindow, interp))

        self.set_observer_modified(-1)

    def get_idx(self, editwindow):
        for i in range(len(self.tab_list)):
            if self.tab_list[i].editwindow == editwindow:
                return i

        return -1

    def get_current_idx(self):
        return self.notebook.GetSelection()

    def get_current_tab(self):
        sel = self.notebook.GetSelection()
        if sel >= 0:
            return self.tab_list[sel]

        else:
            return None

    def get_current_text(self):
        sel = self.notebook.GetSelection()
        if sel >= 0:
            t = self.tab_list[sel].editwindow.GetText()
            return t
        else:
            return None

    def set_new_loaded_file(self, filename, text):
        """Given a filename and its contents (already loaded), setup the
        currently selected tab accordingly.
        """
        
        sel = self.notebook.GetSelection()
        if sel >= 0:
            self.tab_list[sel].editwindow.SetText(text)
            self.tab_list[sel].filename = filename
            
            self.set_tab_modified(sel, False)

    def set_observer_modified(self, idx):
        def observer_modified(ew):
            self.set_tab_modified(self.get_idx(ew), True)
            
        self.tab_list[idx].editwindow.observer_modified = observer_modified

    def set_saved(self, filename):
        """Called when current edit / tab has been written to disk.

        """

        sel = self.notebook.GetSelection()
        if sel >= 0:
            self.tab_list[sel].filename = filename
            self.set_tab_modified(sel, False)

    def set_tab_modified(self, idx, modified):
        if self.tab_list[idx].filename:
            label = os.path.basename(self.tab_list[idx].filename)
        else:
            label = 'Unnamed'

        if modified:
            self.tab_list[idx].modified = True
            label += ' *'

        else:
            self.tab_list[idx].modified = False

        self.notebook.SetPageText(idx, label)


class PythonShell(PythonShellMixin):

    def __init__(self, parent_window, title, icon, devide_app):
        self._devide_app = devide_app
        self._parent_window = parent_window

        self._frame = self._create_frame()
        # set icon
        self._frame.SetIcon(icon)
        # and change the title
        self._frame.SetTitle(title)

        # call ctor of mixin
        PythonShellMixin.__init__(self, self._frame.shell_window)

        self._interp = self._frame.shell_window.interp

        # setup structure we'll use for working with the tabs / edits
        self._tabs = Tabs(self._frame.edit_notebook, self._frame)
        self._tabs.add_existing(self._frame.default_editwindow, self._interp)

        self._bind_events()

        
        # make sure that when the window is closed, we just hide it (teehee)
        wx.EVT_CLOSE(self._frame, self.close_ps_frame_cb)

        #wx.EVT_BUTTON(self._psFrame, self._psFrame.closeButton.GetId(),
        #              self.close_ps_frame_cb)

        # we always start in this directory with our fileopen dialog
        #self._snippetsDir = os.path.join(appDir, 'snippets')
        #wx.EVT_BUTTON(self._psFrame, self._psFrame.loadSnippetButton.GetId(),
        #              self._handlerLoadSnippet)


        self.support_vtk(self._interp)
        self.support_matplotlib(self._interp)
        

        # we can display ourselves
        self.show()

    def close(self):
        PythonShellMixin.close(self, sys.stderr.write)
        
        # take care of the frame
        if self._frame:
            self._frame.Destroy()
            del self._frame

    def show(self):
        self._frame.Show(True)
        self._frame.Iconize(False)        
        self._frame.Raise()

    def hide(self):
        self._frame.Show(False)

    def close_ps_frame_cb(self, event):
        self.hide()

    def _bind_events(self):
        wx.EVT_MENU(self._frame, self._frame.file_new_id,
                    self._handler_file_new)

        wx.EVT_MENU(self._frame, self._frame.file_close_id,
                    self._handler_file_close)
        
        wx.EVT_MENU(self._frame, self._frame.file_open_id,
                    self._handler_file_open)
        
        wx.EVT_MENU(self._frame, self._frame.file_save_id,
                    self._handler_file_save)

        wx.EVT_MENU(self._frame, self._frame.file_saveas_id,
                    self._handler_file_saveas)
            
        wx.EVT_MENU(self._frame, self._frame.run_id,
                    self._handler_file_run)


    def _create_frame(self):
        import resources.python.python_shell_frame
        reload(resources.python.python_shell_frame)
        
        frame = resources.python.python_shell_frame.PyShellFrame(
            self._parent_window, id=-1, title="Dummy", name='DeVIDE')

        return frame

    def _handler_file_new(self, event):
        self._tabs.create_new(self._interp)

    def _handler_file_close(self, event):
        self._tabs.close_current()

    def _handler_file_open(self, event):
        try:
            filename, t = self._open_python_file(self._frame)
        except IOError, e:
            self._devide_app.log_error_with_exception(
                'Could not open file %s: %s' %
                (filename, str(e)))
            
        else:
            if filename:
                self._tabs.set_new_loaded_file(filename, t)
            

    def _handler_file_save(self, event):
        # if we have a filename, just save, if not, do saveas
        current_tab = self._tabs.get_current_tab()
        text = self._tabs.get_current_text()

        try:
            if not current_tab.filename:
                filename = self._saveas_python_file(text, self._frame)
                current_tab.filename = filename
                
            else:
                self._save_python_file(current_tab.filename, text)

        except IOError, e:
            self._devide_app.log_error_with_exception(
                'Could not write file %s: %s' %
                (filename, str(e)))

        else:
            if filename is not None:
                self._tabs.set_saved(current_tab.filename)

    def _handler_file_saveas(self, event):
        text = self._tabs.get_current_text()
        try:
            filename = self._saveas_python_file(text, self._frame)
            
        except IOError, e:
            self._devide_app.log_error_with_exception(
                'Could not write file %s: %s' %
                (filename, str(e)))

        else:
            if filename is not None:
                self._tabs.set_saved(filename)

    def _handler_file_run(self, event):
        t = self._tabs.get_current_text()

        if t is not None:
            self._run_source(t)

        self.set_status_bar_message('Current run completed.')


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

    def inject_locals(self, locals_dict):
        self._interp.locals.update(locals_dict)

    def loadSnippet(self, path):
        try:
            # redirect std thingies so that output appears in the shell win
            self._psFrame.pyShell.redirectStdout()
            self._psFrame.pyShell.redirectStderr()
            self._psFrame.pyShell.redirectStdin()

            # runfile also generates an IOError if it can't load the file
            #execfile(path, globals(), self._psFrame.pyShell.interp.locals)

            # this is quite sneaky, but yields better results especially
            # if there's an exception.
            # IMPORTANT: it's very important that we use a raw string
            # else things go very wonky under windows when double slashes
            # become single slashes and \r and \b and friends do their thing
            self._psFrame.pyShell.run('execfile(r"%s")' %
                                      (path,))
            
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


    def set_status_bar_message(self, message):
        self._frame.statusbar.SetStatusText(message)


