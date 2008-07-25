# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

import itk
import module_kits.itk_kit as itk_kit
from module_base import ModuleBase
from moduleMixins import noConfigModuleMixin
import vtk

class ITKtoVTK(noConfigModuleMixin, ModuleBase):
    """Convert ITK 3D float data to VTK.

    $Revision: 1.5 $
    """

    def __init__(self, moduleManager):
        ModuleBase.__init__(self, moduleManager)


        self._input = None
        self._itk2vtk = None

        noConfigModuleMixin.__init__(
            self,
            {'Module (self)' : self,
             'ImageToVTKImageFilter' : self._itk2vtk})

        self.sync_module_logic_with_config()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        noConfigModuleMixin.close(self)

        ModuleBase.close(self)

        del self._itk2vtk

    def execute_module(self):
        if self._input:

            try:
                shortstring = itk_kit.utils.get_img_type_and_dim_shortstring(
                    self._input)
                
            except TypeError:
                raise TypeError, 'ITKtoVTK requires an ITK image as input.'
            
            witk_template = getattr(itk, 'ImageToVTKImageFilter')
            witk_type = getattr(itk.Image, shortstring)

            try:
                self._itk2vtk = witk_template[witk_type].New()
                
            except KeyError, e:
                raise RuntimeError, 'Unable to instantiate ITK to VTK ' \
                      'converter with type %s.' % \
                      (shortstring,)
            
            else:
                self._input.UpdateOutputInformation()
                self._input.SetBufferedRegion(
                    self._input.GetLargestPossibleRegion())
                self._input.Update()

                itk_kit.utils.setupITKObjectProgress(
                    self, self._itk2vtk,
                    'ImageToVTKImageFilter',
                    'Converting ITK image to VTK image.')
                
                self._itk2vtk.SetInput(self._input)
                self._itk2vtk.Update()

    def get_input_descriptions(self):
        return ('ITK Image',)

    def set_input(self, idx, input_stream):
        self._input = input_stream

    def get_output_descriptions(self):
        return ('VTK Image Data',)

    def get_output(self, idx):
        if self._itk2vtk:
            return self._itk2vtk.GetOutput()
        else:
            return None

    def logic_to_config(self):
        # important so that moduleManager doesn't think our state has changed
        return False
    
    def config_to_logic(self):
        # important so that moduleManager doesn't think our state has changed
        return False
    
    def view_to_config(self):
        pass

    def config_to_view(self):
        pass
    


        
            
