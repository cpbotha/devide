# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

import itk
from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import vtk

class ITKUL3toVTK(noConfigModuleMixin, moduleBase):
    """Convert ITK 3D unsigned long data to VTK.

    $Revision: 1.3 $
    """

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)
        noConfigModuleMixin.__init__(self)

        self._itk2vtk = itk.ImageToVTKImageFilter[itk.Image[itk.UL, 3]].New()

        self._viewFrame = self._createViewFrame(
            {'Module (self)' : self,
             'ImageToVTKImageFilter' : self._itk2vtk})

        self.config_to_logic()
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

        del self._itk2vtk

    def execute_module(self):
        # due to event-driven vs. demand-driven issues, we have to make
        # sure in this converter that ALL data goes through.  if we don't
        # segfault fun ensues.
        #o = self._vtkImporter.GetOutput()
        #o.UpdateInformation()
        #o.SetUpdateExtentToWholeExtent()
        #o.Update()

        self._itk2vtk.Update()

    def get_input_descriptions(self):
        return ('ITK Image (3D, float)',)        

    def set_input(self, idx, inputStream):
        self._itk2vtk.SetInput(inputStream)

    def get_output_descriptions(self):
        return ('VTK Image Data',)

    def get_output(self, idx):
        return self._itk2vtk.GetOutput()

    def logic_to_config(self):
        pass
    
    def config_to_logic(self):
        pass
    
    def view_to_config(self):
        pass

    def config_to_view(self):
        pass


        
            
