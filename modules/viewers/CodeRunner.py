from moduleBase import moduleBase
from moduleMixins import introspectModuleMixin
import moduleUtils

NUMBER_OF_INPUTS = 5
NUMBER_OF_OUTPUTS = 5

class CodeRunner(introspectModuleMixin, moduleBase):

    def __init__(self, module_manager):
        moduleBase.__init__(self, module_manager)

        self.inputs = [None] * NUMBER_OF_INPUTS
        self.outputs = [None] * NUMBER_OF_OUTPUTS

        self._create_view_frame()
        self._bind_events()

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
        pass

    def configToView(self):
        pass

    def executeModule(self):
        pass

    def view(self):
        self._view_frame.Show()
        self._view_frame.Raise()
        
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
                                      self._view_frame.view_frame_panel)

    def _bind_events(self):
        pass

        
        
        
