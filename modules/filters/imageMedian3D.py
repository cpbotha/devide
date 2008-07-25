import genUtils
from module_base import ModuleBase
from moduleMixins import ScriptedConfigModuleMixin
import module_utils
import vtk


class imageMedian3D(ScriptedConfigModuleMixin, ModuleBase):
    
    def __init__(self, module_manager):
        # initialise our base class
        ModuleBase.__init__(self, module_manager)

        self._config.kernelSize = (3, 3, 3)

        configList = [
            ('Kernel size:', 'kernelSize', 'tuple:int,3', 'text',
             'Size of structuring element in pixels.')]

        self._imageMedian3D = vtk.vtkImageMedian3D()

        ScriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
             'vtkImageMedian3D' : self._imageMedian3D})
        
        module_utils.setupVTKObjectProgress(self, self._imageMedian3D,
                                           'Filtering with median')

        self.sync_module_logic_with_config()
        
    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        ScriptedConfigModuleMixin.close(self)
        
        # get rid of our reference
        del self._imageMedian3D

    def execute_module(self):
        self._imageMedian3D.Update()

    def streaming_execute_module(self):
        self._imageMedian3D.Update()

    def get_input_descriptions(self):
        return ('vtkImageData',)

    def set_input(self, idx, inputStream):
        self._imageMedian3D.SetInput(inputStream)

    def get_output_descriptions(self):
        return (self._imageMedian3D.GetOutput().GetClassName(), )

    def get_output(self, idx):
        return self._imageMedian3D.GetOutput()

    def logic_to_config(self):
        self._config.kernelSize = self._imageMedian3D.GetKernelSize()
    
    def config_to_logic(self):
        ks = self._config.kernelSize
        self._imageMedian3D.SetKernelSize(ks[0], ks[1], ks[2])

    

