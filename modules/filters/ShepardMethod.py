from module_base import ModuleBase
from module_mixins import ScriptedConfigModuleMixin
import module_utils
import vtk

class ShephardMethod(ScriptedConfigModuleMixin, ModuleBase):

    """Apply Shepard Method to input.
    
    """
    
    def __init__(self, module_manager):
        # initialise our base class
        ModuleBase.__init__(self, module_manager)


        self._shepardFilter = vtk.vtkShepardMethod()
        
        module_utils.setupVTKObjectProgress(self, self._shepardFilter,
                                           'Applying Shepard Method.')
        
                                           
        self._config.maximum_distance = 1.0
        
                                           
                                           

        configList = [
            ('Kernel size:', 'kernelSize', 'tuple:int,3', 'text',
             'Size of the kernel in x,y,z dimensions.')]

        ScriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
             'vtkImageContinuousDilate3D' : self._imageDilate})

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
        del self._imageDilate

    def get_input_descriptions(self):
        return ('vtkImageData',)

    def set_input(self, idx, inputStream):
        self._imageDilate.SetInput(inputStream)

    def get_output_descriptions(self):
        return (self._imageDilate.GetOutput().GetClassName(), )

    def get_output(self, idx):
        return self._imageDilate.GetOutput()

    def logic_to_config(self):
        self._config.kernelSize = self._imageDilate.GetKernelSize()
    
    def config_to_logic(self):
        ks = self._config.kernelSize
        self._imageDilate.SetKernelSize(ks[0], ks[1], ks[2])
    
    def execute_module(self):
        self._imageDilate.Update()
