from module_base import ModuleBase
from moduleMixins import scriptedConfigModuleMixin
import module_utils
import vtk
import vtkdevide

class extractHDomes(scriptedConfigModuleMixin, ModuleBase):

    def __init__(self, module_manager):
        
        ModuleBase.__init__(self, module_manager)

        self._imageMathSubtractH = vtk.vtkImageMathematics()
        self._imageMathSubtractH.SetOperationToAddConstant()
        
        self._reconstruct = vtkdevide.vtkImageGreyscaleReconstruct3D()
        # second input is marker
        self._reconstruct.SetInput(1, self._imageMathSubtractH.GetOutput())

        self._imageMathSubtractR = vtk.vtkImageMathematics()
        self._imageMathSubtractR.SetOperationToSubtract()

        self._imageMathSubtractR.SetInput(1, self._reconstruct.GetOutput())

        module_utils.setupVTKObjectProgress(self, self._imageMathSubtractH,
                                           'Preparing marker image.')

        module_utils.setupVTKObjectProgress(self, self._reconstruct,
                                           'Performing reconstruction.')

        module_utils.setupVTKObjectProgress(self, self._imageMathSubtractR,
                                           'Subtracting reconstruction.')

        self._config.h = 50

        configList = [
            ('H-dome height:', 'h', 'base:float', 'text',
             'The required difference in brightness between an h-dome and\n'
             'its surroundings.')]

        scriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
             'ImageMath Subtract H' : self._imageMathSubtractH,
             'ImageGreyscaleReconstruct3D' : self._reconstruct,
             'ImageMath Subtract R' : self._imageMathSubtractR})

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
        del self._imageMathSubtractH
        del self._reconstruct
        del self._imageMathSubtractR

    def get_input_descriptions(self):
        return ('Input image (VTK)',)

    def set_input(self, idx, inputStream):
        self._imageMathSubtractH.SetInput(0, inputStream)
        # first input of the reconstruction is the image
        self._reconstruct.SetInput(0, inputStream)
        self._imageMathSubtractR.SetInput(0, inputStream)

    def get_output_descriptions(self):
        return ('h-dome extraction (VTK image)',)

    def get_output(self, idx):
        return self._imageMathSubtractR.GetOutput()

    def logic_to_config(self):
        self._config.h = - self._imageMathSubtractH.GetConstantC()

    def config_to_logic(self):
        self._imageMathSubtractH.SetConstantC( - self._config.h)

    def execute_module(self):
        self._imageMathSubtractR.Update()
        
            

        
        
        
        
    
