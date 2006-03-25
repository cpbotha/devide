# TODO: this shouldn't have the standard ECASH buttons, it's confusing
# let's just override getConfig() to return the texts directly, that's
# far easier. (and better)

# need to combine Editor and Buffer to get autocomplete and what not
# currently we're using EditWindows

import code # deep magic
from moduleBase import moduleBase
from moduleMixins import introspectModuleMixin
import moduleUtils
import sys
import wx

NUMBER_OF_INPUTS = 5
NUMBER_OF_OUTPUTS = 5


class CodeRunner(introspectModuleMixin, moduleBase):

    def __init__(self, module_manager):
        moduleBase.__init__(self, module_manager)

        self.inputs = [None] * NUMBER_OF_INPUTS
        self.outputs = [None] * NUMBER_OF_OUTPUTS

        self._config.scratch_src = self._config.setup_src = \
                                   self._config.execute_src = ''

        self._create_view_frame()
        
        self.interp = self._view_frame.shell_window.interp
        self._view_frame.scratch_editwindow.set_interp(self.interp)
        
        
        self._bind_events()

        self.interp.locals.update(
            {'obj' : self})

        self.configToLogic()
        self.logicToConfig()
        self.configToView()

        self.view()

    def close(self):
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

    def logicToConfig(self):
        pass

    def configToLogic(self):
        pass

    def viewToConfig(self):
        self._config.scratch_src = self._view_frame.scratch_editwindow.\
                                   GetText()
        self._config.setup_src = self._view_frame.setup_editwindow.GetText()
        self._config.execute_src = self._view_frame.execute_editwindow.\
                                   GetText()

    def configToView(self):
        scratch, setup, execute = [self._view_frame.scratch_editwindow,
                                   self._view_frame.setup_editwindow,
                                   self._view_frame.execute_editwindow]

        scratch.SetText(self._config.scratch_src)
        setup.SetText(self._config.setup_src)
        execute.SetText(self._config.execute_src)

    def executeModule(self):
        t = self._view_frame.execute_editwindow.GetText()
        self._run_source(t)

    def view(self):
        self._view_frame.Show()
        self._view_frame.Raise()

    def _bind_events(self):
        self._view_frame.run_button.Bind(
            wx.EVT_BUTTON, self._handler_run_button)

        
    def _create_view_frame(self):
        import resources.python.code_runner_frame
        reload(resources.python.code_runner_frame)

        self._view_frame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager,
            resources.python.code_runner_frame.\
            CodeRunnerFrame)

        self._view_frame.main_splitter.SetMinimumPaneSize(50)

        object_dict = {'Module (self)' : self}

        moduleUtils.createStandardObjectAndPipelineIntrospection(
            self, self._view_frame, self._view_frame.view_frame_panel,
            object_dict, None)

        moduleUtils.createECASButtons(self, self._view_frame,
                                      self._view_frame.view_frame_panel,
                                      executeDefault=False)

    def _handler_run_button(self, evt):
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
        
        interp = self._view_frame.shell_window.interp
        stdin, stdout, stderr = sys.stdin, sys.stdout, sys.stderr
        sys.stdin, sys.stdout, sys.stderr = \
                   interp.stdin, interp.stdout, interp.stderr

        # look: calling class method with interp instance as first parameter
        # comes down to the same as interp calling runsource() as its
        # parent method.
        more = code.InteractiveInterpreter.runsource(
            interp, text, '<input>', 'exec')

        sys.stdin = stdin
        sys.stdout = stdout
        sys.stderr = stderr

        return more

    def run_current_edit(self):
        cew = self._get_current_editwindow()
        text = cew.GetText()
        text = text.replace('\r\n', '\n')
        text = text.replace('\r', '\n')

        self._run_source(text)
        self._view_frame.shell_window.prompt()
