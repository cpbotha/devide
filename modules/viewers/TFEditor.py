# - make our own window control for colour-sequence bar
# - this should also have separate (?) line with HSV colour vertices
# - on this line, there should be vertical lines indicating the current
#   position of all the opacity transfer function vertices
# - abstract floatcanvas-derived linear function editor into wx_kit


from moduleBase import moduleBase
from moduleMixins import introspectModuleMixin
import moduleUtils

class TFEditor(introspectModuleMixin, moduleBase):

    def __init__(self, module_manager):
        moduleBase.__init__(self, module_manager)

        self._volume_input = None
        self._transfer_function = None

        self._view_frame = None
        self._create_view_frame()
        self.view()

    def _create_view_frame(self):
        import resources.python.tfeditorframe
        reload(resources.python.tfeditorframe)

        self._view_frame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager,
            resources.python.tfeditorframe.TFEditorFrame)

        moduleUtils.createStandardObjectAndPipelineIntrospection(
            self, self._view_frame, self._view_frame.view_frame_panel,
            {'Module (self)' : self})

        # add the ECASH buttons
        moduleUtils.createECASButtons(self, self._view_frame,
                                      self._view_frame.view_frame_panel)
        

    def close(self):
        for i in range(len(self.getInputDescriptions())):
            self.setInput(i, None)
        
        self._view_frame.Destroy()
        del self._view_frame

        moduleBase.close(self)

    def getInputDescriptions(self):
        return ('Optional input volume',)

    def getOutputDescriptions(self):
        return ('DeVIDE Transfer Function',)

    def setInput(self, idx, input_stream):
        self._volume_input = input_stream

    def getOutput(self, idx):
        return self._transfer_function
    
    

    def view(self):
        self._view_frame.Show()
        self._view_frame.Raise()

    def executeModel(self):
        pass

        
