# $Id$

from module_base import ModuleBase
from module_mixins import ScriptedConfigModuleMixin
import module_utils
import vtk

class extractImageComponents(ScriptedConfigModuleMixin, ModuleBase):
    
    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        self._extract = vtk.vtkImageExtractComponents()

        module_utils.setup_vtk_object_progress(self, self._extract,
                                           'Extracting components.')
        

        self._config.component1 = 0
        self._config.component2 = 1
        self._config.component3 = 2
        self._config.numberOfComponents = 1
        self._config.fileLowerLeft = False

        configList = [
            ('Component 1:', 'component1', 'base:int', 'text',
             'Zero-based index of first component to extract.'),
            ('Component 2:', 'component2', 'base:int', 'text',
             'Zero-based index of second component to extract.'),
            ('Component 3:', 'component3', 'base:int', 'text',
             'Zero-based index of third component to extract.'),
            ('Number of components:', 'numberOfComponents', 'base:int',
             'choice',
             'Number of components to extract.  Only this number of the '
             'above-specified component indices will be used.',
             ('1', '2', '3'))]

        ScriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
             'vtkImageExtractComponents' : self._extract})

        self.sync_module_logic_with_config()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for input_idx in range(len(self.get_input_descriptions())):
            self.set_input(input_idx, None)

        # this will take care of all display thingies
        ScriptedConfigModuleMixin.close(self)

        ModuleBase.close(self)
        
        # get rid of our reference
        del self._extract

    def get_input_descriptions(self):
        return ('Multi-component vtkImageData',)

    def set_input(self, idx, inputStream):
        self._extract.SetInput(inputStream)

    def get_output_descriptions(self):
        return ('Extracted component vtkImageData',)

    def get_output(self, idx):
        return self._extract.GetOutput()

    def logic_to_config(self):
        # numberOfComponents is 0-based !!
        self._config.numberOfComponents = \
                                        self._extract.GetNumberOfComponents()
        self._config.numberOfComponents -= 1
        
        
        c = self._extract.GetComponents()
        self._config.component1 = c[0]
        self._config.component2 = c[1]
        self._config.component3 = c[2]
        
    def config_to_logic(self):
        # numberOfComponents is 0-based !!
        nc = self._config.numberOfComponents
        nc += 1

        if nc == 1:
            self._extract.SetComponents(self._config.component1)
        elif nc == 2:
            self._extract.SetComponents(self._config.component1,
                                        self._config.component2)
        else:
            self._extract.SetComponents(self._config.component1,
                                        self._config.component2,
                                        self._config.component3)
        
    def execute_module(self):
        self._extract.Update()
        

        
        
        
