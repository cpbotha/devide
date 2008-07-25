import genUtils
from module_base import ModuleBase
from moduleMixins import scriptedConfigModuleMixin
import module_utils
import vtk

class imageGreyDilate(scriptedConfigModuleMixin, ModuleBase):

    def __init__(self, module_manager):
        # initialise our base class
        ModuleBase.__init__(self, module_manager)


        self._imageDilate = vtk.vtkImageContinuousDilate3D()
        
        module_utils.setupVTKObjectProgress(self, self._imageDilate,
                                           'Performing greyscale 3D dilation')
        
                                           
        self._config.kernelSize = (3, 3, 3)


        configList = [
            ('Kernel size:', 'kernelSize', 'tuple:int,3', 'text',
             'Size of the kernel in x,y,z dimensions.')]
        scriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
             'vtkImageContinuousDilate3D' : self._imageDilate})

        self.sync_module_logic_with_config()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)

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

    def streaming_execute_module(self):
        self._imageDilate.Update()

        
