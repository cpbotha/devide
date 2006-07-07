# check python24/lib/code.py - exceptions raised only result in
# printouts.  perhaps we want a real exception?

import code # deep magic
import md5
from moduleBase import moduleBase
from moduleMixins import introspectModuleMixin
import moduleUtils
import sys
import module_kits.wx_kit
from module_kits.wx_kit.python_shell_mixin import PythonShellMixin
import wx

NUMBER_OF_INPUTS = 5
NUMBER_OF_OUTPUTS = 5
EDITWINDOW_LABELS = ['Scratch', 'Setup', 'Execute']

class CodeRunner(introspectModuleMixin, moduleBase, PythonShellMixin):

    def __init__(self, module_manager):
        moduleBase.__init__(self, module_manager)


        self.inputs = [None] * NUMBER_OF_INPUTS
        self.outputs = [None] * NUMBER_OF_OUTPUTS

        self._config.scratch_src = self._config.setup_src = \
                                   self._config.execute_src = ''

        self._config_srcs = ['scratch_src',
                             'setup_src',
                             'execute_src']

        # these are the real deals, i.e. the underlying logic
        self._src_scratch = self._src_setup = self._src_execute = ''
        self._srcs = ['_src_scratch', '_src_setup', '_src_execute']

        # we use this to determine whether the current setup src has been
        # executed or not
        self._md5_setup_src = ''

        self._create_view_frame()

        PythonShellMixin.__init__(self, self._view_frame.shell_window,
                                  module_manager)

        moduleUtils.createECASButtons(self, self._view_frame,
                                      self._view_frame.view_frame_panel,
                                      executeDefault=False)

        # more convenience bindings
        self._editwindows = [self._view_frame.scratch_editwindow,
                             self._view_frame.setup_editwindow,
                             self._view_frame.execute_editwindow]
        
        self.interp = self._view_frame.shell_window.interp

        # set interpreter on all three our editwindows
        for ew in self._editwindows:
            ew.set_interp(self.interp)
        
        self._bind_events()

        self.interp.locals.update(
            {'obj' : self})

        # initialise macro packages
        self.support_vtk(self.interp)
        self.support_matplotlib(self.interp)

        self.configToLogic()
        self.logicToConfig()
        self.configToView()

        self.view()

    def close(self):
        # parameter is exception_printer method
        PythonShellMixin.close(self,
                               self._moduleManager.log_error_with_exception)
        
        for i in range(len(self.getInputDescriptions())):
            self.setInput(i, None)

        self._view_frame.Destroy()
        del self._view_frame

        moduleBase.close(self)

    def getInputDescriptions(self):
        return ('Any input',) * NUMBER_OF_INPUTS

    def getOutputDescriptions(self):
        return ('Dynamic output',) * NUMBER_OF_OUTPUTS

    def setInput(self, idx, input_stream):
        self.inputs[idx] = input_stream

    def getOutput(self, idx):
        return self.outputs[idx]

    def viewToConfig(self):
        for ew, cn, i in zip(self._editwindows, self._config_srcs,
                             range(len(self._editwindows))):
            
            setattr(self._config, cn, ew.GetText())
            self.set_editwindow_modified(i, False)
        
    def configToView(self):
        for ew, cn, i in zip(self._editwindows, self._config_srcs,
                             range(len(self._editwindows))):
            
            ew.SetText(getattr(self._config, cn))
            self.set_editwindow_modified(i, False)

    def configToLogic(self):
        logic_changed = False

        for cn,ln in zip(self._config_srcs, self._srcs):
            c = getattr(self._config, cn)
            l = getattr(self, ln)
            if c != l:
                setattr(self, ln, c)
                logic_changed = True

        return logic_changed

    def logicToConfig(self):
        config_changed = False

        for cn,ln in zip(self._config_srcs, self._srcs):
            c = getattr(self._config, cn)
            l = getattr(self, ln)
            if l != c:
                setattr(self._config, cn, l)
                config_changed = True

        return config_changed

    def executeModule(self):
        # we only attempt running setup_src if its md5 is different from
        # that of the previous setup_src that we attempted to run
        hd = md5.md5(self._src_setup).hexdigest
        if hd != self._md5_setup_src:
            self._md5_setup_src = hd
            self._run_source(self._src_setup, self._view_frame.shell_window)
            
        self._run_source(self._src_execute)

    def view(self):
        self._view_frame.Show()
        self._view_frame.Raise()

    def _bind_events(self):
        wx.EVT_MENU(self._view_frame, self._view_frame.file_open_id,
                    self._handler_file_open)
        wx.EVT_MENU(self._view_frame, self._view_frame.file_save_id,
                    self._handler_file_save)
            
        wx.EVT_MENU(self._view_frame, self._view_frame.run_id,
                    self._handler_run)

        for i in range(len(self._editwindows)):
            def observer_modified(ew, i=i):
                self.set_editwindow_modified(i, True)
                
            self._editwindows[i].observer_modified = observer_modified

        
    def _create_view_frame(self):
        import resources.python.code_runner_frame
        reload(resources.python.code_runner_frame)

        self._view_frame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager,
            resources.python.code_runner_frame.\
            CodeRunnerFrame)

        self._view_frame.main_splitter.SetMinimumPaneSize(50)

    def _handler_file_open(self, evt):
        try:
            filename, t = self._open_python_file(self._view_frame)
                
        except IOError, e:
            self._moduleManager.log_error_with_exception(
                'Could not open file %s into CodeRunner edit: %s' %
                (filename, str(e)))

        else:
            if filename is not None:
                cew = self._get_current_editwindow()
                cew.SetText(t)
                self._view_frame.statusbar.SetStatusText(
                    'Loaded %s into current edit.' % (filename,))

    def _handler_file_save(self, evt):
        try:
            cew = self._get_current_editwindow()
            filename = self._saveas_python_file(cew.GetText(),
                                                self._view_frame)
            if filename is not None:
                self._view_frame.statusbar.SetStatusText(
                    'Saved current edit to %s.' % (filename,))
            
        except IOError, e:
            self._moduleManager.log_error_with_exception(
                'Could not save CodeRunner edit to file %s: %s' %
                (filename, str(e)))

    def _handler_run(self, evt):
        self.run_current_edit()

    def _get_current_editwindow(self):
        sel = self._view_frame.edit_notebook.GetSelection()
        return [self._view_frame.scratch_editwindow,
                self._view_frame.setup_editwindow,
                self._view_frame.execute_editwindow][sel]

    def run_current_edit(self):
        cew = self._get_current_editwindow()
        text = cew.GetText()

        self._run_source(text)

        self._view_frame.statusbar.SetStatusText(
            'Current edit run completed.')

    def set_editwindow_modified(self, idx, modified):
        pt = EDITWINDOW_LABELS[idx]

        if modified:
            pt += ' *'
            
        self._view_frame.edit_notebook.SetPageText(idx, pt)
        
        
        
