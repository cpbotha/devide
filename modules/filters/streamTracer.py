import input_array_choice_mixin
from input_array_choice_mixin import InputArrayChoiceMixin
from module_base import ModuleBase
from module_mixins import ScriptedConfigModuleMixin
import module_utils
import vtk

INTEG_TYPE = ['RK2', 'RK4', 'RK45']
INTEG_TYPE_TEXTS = ['Runge-Kutta 2', 'Runge-Kutta 4', 'Runge-Kutta 45']
ARRAY_IDX = 0

class streamTracer(ScriptedConfigModuleMixin, InputArrayChoiceMixin, ModuleBase):
    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)
        InputArrayChoiceMixin.__init__(self)

        # 0 = RK2
        # 1 = RK4
        # 2 = RK45
        self._config.integrator = INTEG_TYPE.index('RK2')

        configList = [
            ('Vectors selection:', 'vectorsSelection', 'base:str', 'choice',
             'The attribute that will be used as vectors for the warping.',
             (input_array_choice_mixin.DEFAULT_SELECTION_STRING,)),
            ('Integrator type:', 'integrator', 'base:int', 'choice',
             'Select an integrator for the streamlines.',
             INTEG_TYPE_TEXTS)]

        self._streamTracer = vtk.vtkStreamTracer() 

        ScriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
             'vtkStreamTracer' : self._streamTracer})

        module_utils.setup_vtk_object_progress(self, self._streamTracer,
                                           'Tracing stream lines.')
        
        self.sync_module_logic_with_config()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for input_idx in range(len(self.get_input_descriptions())):
            self.set_input(input_idx, None)

        # this will take care of all display thingies
        ScriptedConfigModuleMixin.close(self)
        
        # get rid of our reference
        del self._streamTracer

    def execute_module(self):
        self._streamTracer.Update()
        
        if self.view_initialised:
            choice = self._getWidget(0)
            self.iac_execute_module(self._streamTracer, choice,
                    ARRAY_IDX)

    def get_input_descriptions(self):
        return ('VTK Vector dataset', 'VTK source geometry')

    def set_input(self, idx, inputStream):
        if idx == 0:
            self._streamTracer.SetInput(inputStream)
            
        else:
            self._streamTracer.SetSource(inputStream)

    def get_output_descriptions(self):
        return ('Streamlines polydata',)

    def get_output(self, idx):
        return self._streamTracer.GetOutput()

    def logic_to_config(self):
        self._config.integrator = self._streamTracer.GetIntegratorType()
    
        # this will extract the possible choices
        self.iac_logic_to_config(self._streamTracer, ARRAY_IDX)

    def config_to_logic(self):
        self._streamTracer.SetIntegratorType(self._config.integrator)

        # it seems that array_idx == 1 refers to vectors
        # array_idx 0 gives me only the x-component of multi-component
        # arrays
        self.iac_config_to_logic(self._streamTracer, ARRAY_IDX)

    def config_to_view(self):
        # first get our parent mixin to do its thing
        ScriptedConfigModuleMixin.config_to_view(self)

        choice = self._getWidget(0)
        self.iac_config_to_view(choice)

