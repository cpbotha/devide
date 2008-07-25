import genUtils
from module_base import ModuleBase
from moduleMixins import noConfigModuleMixin
import moduleUtils
import wx
import vtk

class imageGradientMagnitude(noConfigModuleMixin, ModuleBase):

    def __init__(self, moduleManager):
        # initialise our base class
        ModuleBase.__init__(self, moduleManager)


        self._imageGradientMagnitude = vtk.vtkImageGradientMagnitude()
        self._imageGradientMagnitude.SetDimensionality(3)
        
        moduleUtils.setupVTKObjectProgress(self, self._imageGradientMagnitude,
                                           'Calculating gradient magnitude')

        noConfigModuleMixin.__init__(
            self,
            {'Module (self)' : self,
             'vtkImageGradientMagnitude' : self._imageGradientMagnitude})

        self.sync_module_logic_with_config()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        noConfigModuleMixin.close(self)

        ModuleBase.close(self)
        
        # get rid of our reference
        del self._imageGradientMagnitude

    def get_input_descriptions(self):
        return ('vtkImageData',)

    def set_input(self, idx, inputStream):
        self._imageGradientMagnitude.SetInput(inputStream)

    def get_output_descriptions(self):
        return (self._imageGradientMagnitude.GetOutput().GetClassName(), )

    def get_output(self, idx):
        return self._imageGradientMagnitude.GetOutput()

    def logic_to_config(self):
        pass
    
    def config_to_logic(self):
        pass
    
    def view_to_config(self):
        pass

    def config_to_view(self):
        pass
    
    def execute_module(self):
        self._imageGradientMagnitude.Update()
        
