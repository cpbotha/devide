import genUtils
from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import moduleUtils
import wx
import vtk
import vtkdevide


class greyReconstruct(noConfigModuleMixin, moduleBase):
    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)
        noConfigModuleMixin.__init__(self)

        self._greyReconstruct = vtkdevide.vtkImageGreyscaleReconstruct3D()
        
        moduleUtils.setupVTKObjectProgress(
            self, self._greyReconstruct,
            'Performing greyscale reconstruction')
        

        self._viewFrame = self._createViewFrame(
            {'Module (self)' : self,
             'vtkImageGreyscaleReconstruct3D' : self._greyReconstruct})

        # pass the data down to the underlying logic
        self.config_to_logic()
        # and all the way up from logic -> config -> view to make sure
        self.logic_to_config()
        self.config_to_view()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        noConfigModuleMixin.close(self)

        moduleBase.close(self)
        
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
        
    
