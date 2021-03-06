# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

import itk
from module_base import ModuleBase
from module_mixins import NoConfigModuleMixin
import vtk

class VTKtoITKF3(NoConfigModuleMixin, ModuleBase):

    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)


        # setup the pipeline
        self._imageCast = vtk.vtkImageCast()
        self._imageCast.SetOutputScalarTypeToFloat()

        self._vtk2itk = itk.VTKImageToImageFilter[itk.Image[itk.F, 3]].New()
        self._vtk2itk.SetInput(self._imageCast.GetOutput())

        NoConfigModuleMixin.__init__(
            self,
            {'Module (self)' : self,
             'vtkImageCast' : self._imageCast,
             'VTKImageToImageFilter' : self._vtk2itk})
        
        self.sync_module_logic_with_config()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for input_idx in range(len(self.get_input_descriptions())):
            self.set_input(input_idx, None)

        # this will take care of all display thingies
        NoConfigModuleMixin.close(self)

        ModuleBase.close(self)

        del self._imageCast
        del self._vtk2itk

    def execute_module(self):
        # the whole connectvtkitk thingy is quite shaky and was really
        # designed for demand-driven use.  using it in an event-driven
        # environment, we have to make sure it does exactly what we want
        # it to do.  one day, we'll implement contracts and do this
        # differently.

        #o = self._itkImporter.GetOutput()
        #o.UpdateOutputInformation()
        #o.SetRequestedRegionToLargestPossibleRegion()
        #o.Update()

        self._vtk2itk.Update()

    def get_input_descriptions(self):
        return ('VTK Image Data',)

    def set_input(self, idx, inputStream):
        self._imageCast.SetInput(inputStream)

    def get_output_descriptions(self):
        return ('ITK Image (3D, float)',)

    def get_output(self, idx):
        return self._vtk2itk.GetOutput()

    def logic_to_config(self):
        pass
    
    def config_to_logic(self):
        pass
    
    def view_to_config(self):
        pass

    def config_to_view(self):
        pass
    

        
            
