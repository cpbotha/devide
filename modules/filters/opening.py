import gen_utils
from module_base import ModuleBase
from module_mixins import ScriptedConfigModuleMixin
import module_utils
import vtk

class opening(ScriptedConfigModuleMixin, ModuleBase):

    def __init__(self, module_manager):
        # initialise our base class
        ModuleBase.__init__(self, module_manager)

        self._imageDilate = vtk.vtkImageContinuousDilate3D()
        self._imageErode = vtk.vtkImageContinuousErode3D()
        self._imageDilate.SetInput(self._imageErode.GetOutput())
        
        module_utils.setupVTKObjectProgress(self, self._imageDilate,
                                           'Performing greyscale 3D dilation')
        

        module_utils.setupVTKObjectProgress(self, self._imageErode,
                                           'Performing greyscale 3D erosion')
        

        self._config.kernelSize = (3, 3, 3)


        configList = [
            ('Kernel size:', 'kernelSize', 'tuple:int,3', 'text',
             'Size of the kernel in x,y,z dimensions.')]

        ScriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
             'vtkImageContinuousDilate3D' : self._imageDilate,
             'vtkImageContinuousErode3D' : self._imageErode})

        self.sync_module_logic_with_config()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        ScriptedConfigModuleMixin.close(self)

        ModuleBase.close(self)
        
        # get rid of our reference
        del self._imageDilate
        del self._imageErode

    def get_input_descriptions(self):
        return ('vtkImageData',)

    def set_input(self, idx, inputStream):
        self._imageErode.SetInput(inputStream)

    def get_output_descriptions(self):
        return ('Opened image (vtkImageData)',)

    def get_output(self, idx):
        return self._imageDilate.GetOutput()

    def logic_to_config(self):
        # if the user's futzing around, she knows what she's doing...
        # (we assume that the dilate/erode pair are in sync)
        self._config.kernelSize = self._imageErode.GetKernelSize()
    
    def config_to_logic(self):
        ks = self._config.kernelSize
        self._imageDilate.SetKernelSize(ks[0], ks[1], ks[2])
        self._imageErode.SetKernelSize(ks[0], ks[1], ks[2])
    
    def execute_module(self):
        self._imageErode.Update()
        
        self._imageDilate.Update()
        


