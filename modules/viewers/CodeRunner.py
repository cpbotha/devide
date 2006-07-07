# check python24/lib/code.py - exceptions raised only result in
# printouts.  perhaps we want a real exception?

import code # deep magic
import md5
from moduleBase import moduleBase
from moduleMixins import introspectModuleMixin
import moduleUtils
import sys
import wx

NUMBER_OF_INPUTS = 5
NUMBER_OF_OUTPUTS = 5
EDITWINDOW_LABELS = ['Scratch', 'Setup', 'Execute']

class CodeRunner(introspectModuleMixin, moduleBase):


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

        # init close handlers
        self.close_handlers = []

        # initialise macro packages
        self.support_vtk()
        self.support_matplotlib()

        self.configToLogic()
        self.logicToConfig()
        self.configToView()

        self.view()

    def close(self):
        for ch in self.close_handlers:
            try:
                ch()
            except Exception, e:
                self._moduleManager.log_error_with_exception(
                    'Exception during CodeRunner close_handlers: %s' %
                    (str(e),))
        
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
            self._run_source(self._src_setup)
            
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
        fd = wx.FileDialog(
            self._view_frame,
            'Select file to open into current edit',
            wildcard='*.py', style=wx.OPEN)

        if fd.ShowModal() == wx.ID_OK:
            filename = fd.GetPath()
            
            cew = self._get_current_editwindow()
            try:
                f = open(filename, 'r')
                
                t = f.read()
                # replace stupid DOS CR/LF with newline
                t = t.replace('\r\n', '\n')
                # any CRs that are left are nuked
                t = t.replace('\r', '')

                cew.SetText(t)
                f.close()
                
            except IOError, e:
                self._moduleManager.log_error_with_exception(
                    'Could not open file %s into CodeRunner edit: %s' %
                    (filename, str(e)))

            else:
                self._view_frame.statusbar.SetStatusText(
                    'Loaded %s into current edit.' % (filename,))

    def _handler_file_save(self, evt):
        fd = wx.FileDialog(
            self._view_frame,
            'Select filename to save current edit to',
            wildcard='*.py', style=wx.SAVE)

        if fd.ShowModal() == wx.ID_OK:
            filename = fd.GetPath()
            
            cew = self._get_current_editwindow()
            try:
                f = open(filename, 'w')
                t = cew.GetText()
                f.write(t)
                f.close()
                
            except IOError, e:
                self._moduleManager.log_error_with_exception(
                    'Could not save CodeRunner edit to file %s: %s' %
                    (filename, str(e)))

            else:
                self._view_frame.statusbar.SetStatusText(
                    'Saved current edit to %s.' % (filename,))
        
    def _handler_run(self, evt):
        self.run_current_edit()

    def _get_current_editwindow(self):
        sel = self._view_frame.edit_notebook.GetSelection()
        return [self._view_frame.scratch_editwindow,
                self._view_frame.setup_editwindow,
                self._view_frame.execute_editwindow][sel]


    def _run_source(self, text):
        """Compile and run the source given in text in the shell interpreter's
        local namespace.

        The idiot pyshell goes through the whole shell.push -> interp.push
        -> interp.runsource -> InteractiveInterpreter.runsource hardcoding the
        'mode' parameter (effectively) to 'single', thus breaking multi-line
        definitions and whatnot.

        Here we do some deep magic (ha ha) to externally override the interp
        runsource.  Python does completely rule.
        """

        text = text.replace('\r\n', '\n')
        text = text.replace('\r', '\n')
        
        interp = self._view_frame.shell_window.interp
        stdin, stdout, stderr = sys.stdin, sys.stdout, sys.stderr
        sys.stdin, sys.stdout, sys.stderr = \
                   interp.stdin, interp.stdout, interp.stderr

        # look: calling class method with interp instance as first parameter
        # comes down to the same as interp calling runsource() as its
        # parent method.
        more = code.InteractiveInterpreter.runsource(
            interp, text, '<input>', 'exec')

        # make sure the user can type again
        self._view_frame.shell_window.prompt()

        sys.stdin = stdin
        sys.stdout = stdout
        sys.stderr = stderr

        return more

    def output_text(self, text):
        self._view_frame.shell_window.write(text + '\n')
        self._view_frame.shell_window.prompt()

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
        
        
    def support_vtk(self):
        if hasattr(self, 'vtk_renderwindows'):
            return

        import module_kits
        if 'vtk_kit' not in module_kits.module_kit_list:
            self.output_text('No VTK support.')
            return
        
        from module_kits import vtk_kit
        vtk = vtk_kit.vtk

        def get_render_info(instance_name):
            instance = self._moduleManager.get_instance(instance_name)

            if instance is None:
                return None
            
            class RenderInfo:
                pass

            render_info = RenderInfo()

            render_info.renderer = instance.get_3d_renderer()
            render_info.render_window = instance.get_3d_render_window()
            render_info.interactor = instance.\
                                     get_3d_render_window_interactor()
            

            return render_info

        new_dict = {'vtk' : vtk,
                    'vtk_get_render_info' : get_render_info}

        self.interp.locals.update(new_dict)
        self.__dict__.update(new_dict)

        self.output_text('VTK support loaded.')

    def support_matplotlib(self):
        if hasattr(self, 'mpl_figure_handles'):
            return

        import module_kits

        if 'matplotlib_kit' not in module_kits.module_kit_list:
            self.output_text('No matplotlib support.')
            return

        from module_kits import matplotlib_kit
        pylab = matplotlib_kit.pylab
        
        # setup shutdown logic ########################################
        self.mpl_figure_handles = []

        def mpl_close_handler():
            for fh in self.mpl_figure_handles:
                pylab.close(fh)
        
        self.close_handlers.append(mpl_close_handler)
        
        # hook our mpl_new_figure method ##############################

        # mpl_new_figure hook so that all created figures are registered
        # and will be closed when the module is closed
        def mpl_new_figure(*args):
            handle = pylab.figure(*args)
            self.mpl_figure_handles.append(handle)
            return handle

        def mpl_close_figure(handle):
            """Close matplotlib figure.
            """
            pylab.close(handle)
            if handle in self.mpl_figure_handles:
                idx = self.mpl_figure_handles(handle)
                del self.mpl_figure_handles[idx]

        # replace our hook's documentation with the 'real' documentation
        mpl_new_figure.__doc__ = pylab.figure.__doc__

        # stuff the required symbols into the module's namespace ######
        new_dict = {'matplotlib' : matplotlib_kit.matplotlib,
                    'pylab' : matplotlib_kit.pylab,
                    'mpl_new_figure' : mpl_new_figure,
                    'mpl_close_figure' : mpl_close_figure}
        
        self.interp.locals.update(new_dict)
        self.__dict__.update(new_dict)

        self.output_text('matplotlib support loaded.')

        
