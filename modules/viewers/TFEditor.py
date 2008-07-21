# - make our own window control for colour-sequence bar
# - this should also have separate (?) line with HSV colour vertices
# - on this line, there should be vertical lines indicating the current
#   position of all the opacity transfer function vertices
# - abstract floatcanvas-derived linear function editor into wx_kit


from moduleBase import moduleBase
from moduleMixins import IntrospectModuleMixin
import moduleUtils

class TFEditor(IntrospectModuleMixin, moduleBase):

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


        oc = self._view_frame.opacity_canvas

        # do initial drawing setup
        oc.AddLine(((0, 0), (100, 0)))
        oc.AddLine(((0, 0), (0, 100)))

        # this should be dependent on some internal datastructure with
        # points
        oc.AddCircle((0, 0), 5)
        oc.AddCircle((30, 0), 5)
        oc.AddCircle((100,0), 5)

        #Poly.Bind(FloatCanvas.EVT_FC_LEFT_DOWN, MyCallback)

        oc.ZoomToBB()
        

    def close(self):
        for i in range(len(self.get_input_descriptions())):
            self.set_input(i, None)
        
        self._view_frame.Destroy()
        del self._view_frame

        moduleBase.close(self)

    def get_input_descriptions(self):
        return ('Optional input volume',)

    def get_output_descriptions(self):
        return ('DeVIDE Transfer Function',)

    def set_input(self, idx, input_stream):
        self._volume_input = input_stream

    def get_output(self, idx):
        return self._transfer_function
    
    

    def view(self):
        self._view_frame.Show()
        self._view_frame.Raise()

    def executeModel(self):
        pass

        
