from module_base import ModuleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtk

INTEG_TYPE = ['RK2', 'RK4', 'RK45']
INTEG_TYPE_TEXTS = ['Runge-Kutta 2', 'Runge-Kutta 4', 'Runge-Kutta 45']

class streamTracer(scriptedConfigModuleMixin, ModuleBase):
    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        # 0 = RK2
        # 1 = RK4
        # 2 = RK45
        self._config.integrator = INTEG_TYPE.index('RK2')

        configList = [
            ('Integrator type:', 'integrator', 'base:int', 'choice',
             'Select an integrator for the streamlines.',
             INTEG_TYPE_TEXTS)]

        self._streamTracer = vtk.vtkStreamTracer() 

        scriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
             'vtkStreamTracer' : self._streamTracer})

        moduleUtils.setupVTKObjectProgress(self, self._streamTracer,
                                           'Tracing stream lines.')
        
        self.sync_module_logic_with_config()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)
        
        # get rid of our reference
        del self._streamTracer

    def execute_module(self):
        self._streamTracer.Update()
        

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
    
    def config_to_logic(self):
        self._streamTracer.SetIntegratorType(self._config.integrator)

        

        
