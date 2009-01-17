from module_base import ModuleBase
from module_mixins import IntrospectModuleMixin
import module_utils

class QuickInfo(IntrospectModuleMixin, ModuleBase):

    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        self._input = None

        self._view_frame = None
        self._create_view_frame()
        self.view()

        self.view_initialised = True

    def _create_view_frame(self):
        import resources.python.quick_info_frames
        reload(resources.python.quick_info_frames)

        self._view_frame = module_utils.instantiate_module_view_frame(
                self, self._module_manager,
                resources.python.quick_info_frames.QuickInfoFrame)

        module_utils.create_standard_object_introspection(
                self, self._view_frame,
                self._view_frame.view_frame_panel,
                {'Module (self)' : self})

        module_utils.create_eoca_buttons(self, self._view_frame,
                                        self._view_frame.view_frame_panel)


    def close(self):
        for i in range(len(self.get_input_descriptions())):
            self.set_input(i, None)
        
        self._view_frame.Destroy()
        del self._view_frame

        ModuleBase.close(self)

    def get_input_descriptions(self):
        return ('Any DeVIDE data',)

    def get_output_descriptions(self):
        return ()

    def set_input(self, idx, input_stream):
        self._input = input_stream

    def get_output(self, idx):
        raise RuntimeError

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
        ot = self._view_frame.output_text
        ot.SetValue('line 1\nline2')

        


