# - make our own window control for colour-sequence bar
# - this should also have separate (?) line with HSV colour vertices
# - on this line, there should be vertical lines indicating the current
#   position of all the opacity transfer function vertices
# - abstract floatcanvas-derived linear function editor into wx_kit


from moduleBase import moduleBase
from moduleMixins import IntrospectModuleMixin
import moduleUtils
from external import transfer_function_widget as tfw

class TFEditor(IntrospectModuleMixin, moduleBase):

    def __init__(self, module_manager):
        moduleBase.__init__(self, module_manager)

        self._volume_input = None
        self._transfer_function = None

        # list of tuples, where each tuple (scalar_value, (r,g,b,a))
        self._config.transfer_function = []

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
        moduleUtils.create_eoca_buttons(self, self._view_frame,
                                        self._view_frame.view_frame_panel)

        def handler_blaat(event):
            tf_widget = event.GetEventObject() # the tf_widget
            ret = tf_widget.get_current_point_info()
            if not ret is None:
                val, col, opacity = ret
                vf = self._view_frame
                vf.colour_button.SetBackgroundColour(col)
                vf.cur_scalar_text.SetValue('%.2f' % (val,))
                vf.cur_col_text.SetValue(str(col))
                vf.cur_opacity_text.SetValue('%.2f' % (opacity,))

        self._view_frame.tf_widget.Bind(tfw.EVT_CUR_PT_CHANGED,
                handler_blaat)


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


    def logic_to_config(self):
        pass

    def config_to_logic(self):
        pass

    def view_to_config(self):
        pass

    def config_to_view(self):
        pass

    def view(self):
        self._view_frame.Show()
        self._view_frame.Raise()

    def execute_module(self):
        pass

        
