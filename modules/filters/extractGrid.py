from module_base import ModuleBase
from module_mixins import ScriptedConfigModuleMixin
import module_utils
import vtk
import vtkdevide

class extractGrid(ScriptedConfigModuleMixin, ModuleBase):
    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        self._config.sampleRate = (1, 1, 1)

        configList = [
            ('Sample rate:', 'sampleRate', 'tuple:int,3', 'tupleText',
             'Subsampling rate.')]



        self._extractGrid = vtkdevide.vtkPVExtractVOI()
        
        module_utils.setupVTKObjectProgress(self, self._extractGrid,
                                           'Subsampling structured grid.')

        ScriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
             'vtkExtractGrid' : self._extractGrid})

        self.sync_module_logic_with_config()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        ScriptedConfigModuleMixin.close(self)
        
        # get rid of our reference
        del self._extractGrid

    def execute_module(self):
        self._extractGrid.Update()
        

    def get_input_descriptions(self):
        return ('VTK Dataset',)

    def set_input(self, idx, inputStream):
        self._extractGrid.SetInput(inputStream)

    def get_output_descriptions(self):
        return ('Subsampled VTK Dataset',)

    def get_output(self, idx):
        return self._extractGrid.GetOutput()

    def logic_to_config(self):
        self._config.sampleRate = self._extractGrid.GetSampleRate()
    
    def config_to_logic(self):
        self._extractGrid.SetSampleRate(self._config.sampleRate)
        
