from module_base import ModuleBase
from module_mixins import NoConfigModuleMixin
import module_utils

class PassThrough(NoConfigModuleMixin, ModuleBase):
    def __init__(self, module_manager):
        # initialise our base class
        ModuleBase.__init__(self, module_manager)

        NoConfigModuleMixin.__init__(
            self, {'Module (self)' : self})

        self.sync_module_logic_with_config()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for input_idx in range(len(self.get_input_descriptions())):
            self.set_input(input_idx, None)

        # this will take care of all display thingies
        NoConfigModuleMixin.close(self)
        
    def get_input_descriptions(self):
        return ('Anything',)

    def set_input(self, idx, input_stream):
        self._input = input_stream

    def get_output_descriptions(self):
        return ('Same as input', )

    def get_output(self, idx):
        return self._input

    def execute_module(self):
        pass
