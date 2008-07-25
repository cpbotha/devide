import genUtils
from module_base import ModuleBase
from moduleMixins import NoConfigModuleMixin
import module_utils
import vtk
import vtkdevide

class greyReconstruct(NoConfigModuleMixin, ModuleBase):
    def __init__(self, module_manager):
        # initialise our base class
        ModuleBase.__init__(self, module_manager)


        self._greyReconstruct = vtkdevide.vtkImageGreyscaleReconstruct3D()

        NoConfigModuleMixin.__init__(
            self,
            {'Module (self)' : self,
             'vtkImageGreyscaleReconstruct3D' : self._greyReconstruct})
        
        module_utils.setupVTKObjectProgress(
            self, self._greyReconstruct,
            'Performing greyscale reconstruction')

        self.sync_module_logic_with_config()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        NoConfigModuleMixin.close(self)

        ModuleBase.close(self)
        
        # get rid of our reference
        del self._greyReconstruct

    def get_input_descriptions(self):
        return ('Mask image I (VTK)', 'Marker image J (VTK)')

    def set_input(self, idx, inputStream):
        if idx == 0:
            self._greyReconstruct.SetInput1(inputStream)
        else:
            self._greyReconstruct.SetInput2(inputStream)

    def get_output_descriptions(self):
        return ('Reconstructed image (VTK)', )

    def get_output(self, idx):
        return self._greyReconstruct.GetOutput()

    def logic_to_config(self):
        pass
    
    def config_to_logic(self):
        pass
    
    def view_to_config(self):
        pass

    def config_to_view(self):
        pass
    
    def execute_module(self):
        self._greyReconstruct.Update()
        
    
