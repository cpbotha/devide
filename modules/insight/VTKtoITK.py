# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

import itk
import module_kits.itk_kit as itk_kit
from module_base import ModuleBase
from moduleMixins import scriptedConfigModuleMixin
import vtk

class VTKtoITK(scriptedConfigModuleMixin, ModuleBase):

    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        self._input = None

        self._image_cast = vtk.vtkImageCast()
        self._vtk2itk = None
        # this stores the short_string of the current converter, e.g.
        # F3 or US3, etc.
        self._vtk2itk_short_string = None

        self._config.autotype = True
        # this will store the current type as full text, e.g. "unsigned char"
        self._config.type = 'float'

        config_list = [
            ('AutoType:', 'autotype', 'base:bool', 'checkbox',
             'If activated, output data type is set to '
             'input type.'),
            ('Data type:', 'type', 'base:str', 'choice',
             'Data will be cast to this type if AutoType is not used.',
             ['float', 'signed short', 'unsigned long'])]

        scriptedConfigModuleMixin.__init__(self, config_list,
                                           {'Module (self)' : self})

        self.sync_module_logic_with_config()
        
    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)
        # and the baseclass close
        ModuleBase.close(self)
            
        del self._image_cast
        del self._vtk2itk

    def execute_module(self):
        if self._input:

            # calculate input type
            try:
                self._input.Update()                
                if self._input.IsA('vtkImageData'):
                    input_type = self._input.GetScalarTypeAsString()
            except AttributeError:
                raise TypeError, 'VTKtoITK requires VTK image data as input.'

            # input_type is a text repr, e.g. 'float' or 'unsigned char'

            # now calculate output type
            if self._config.autotype:
                output_type = input_type

            else:
                # this is also just a text description
                output_type = self._config.type

            dims = self._input.GetDataDimension()

            # create shortstring (e.g. US3, SS2)
            short_string_type = ''.join([i[0].upper()
                                         for i in output_type.split()])
            if short_string_type == 'S':
                short_string_type = 'SS'


            if short_string_type.startswith('V'):
                short_string = '%s%s%s' % (short_string_type, dims,
                        dims)
            else:
                short_string = '%s%s' % (short_string_type, dims)


            # we could cache this as shown below, but experience shows
            # that the connection module often gets confused when its
            # input data remains the same w.r.t. type, but changes in
            # extent for instance.
            #if short_string != self._vtk2itk_short_string:
            self._vtk2itk = itk.VTKImageToImageFilter[
                getattr(itk.Image, short_string)].New()
            self._vtk2itk_short_string = short_string
                
            if output_type == input_type:
                # we don't need the cast
                self._vtk2itk.SetInput(self._input)
                
            else:
                # we do need the cast
                self._image_cast.SetInput(self._input)

                # turn unsigned char into UnsignedChar, but signed
                # short into Short.
                # output_type is e.g. "signed short"
                # first break the list up, capitalise first letters
                captsl = ['%s%s' % (i[0].upper(), i[1:]) 
                         for i in output_type.split()]
                # however, VTK doesn't have the Signed bit! (so we
                # just want "Short")
                if captsl[0] == "Signed":
                    del captsl[0]
                # then join them together
                vtk_type_string = ''.join(captsl)
                # cast function
                cast_function = getattr(
                    self._image_cast,
                    'SetOutputScalarTypeTo%s' % (vtk_type_string,))
                
                cast_function()

                # and connect it up
                self._vtk2itk.SetInput(self._image_cast.GetOutput())

        self._vtk2itk.Update()

    def get_input_descriptions(self):
        return ('VTK Image Data',)

    def set_input(self, idx, input_stream):
        self._input = input_stream
        
    def get_output_descriptions(self):
        return ('ITK Image (3D',)

    def get_output(self, idx):
        if self._vtk2itk:
            return self._vtk2itk.GetOutput()
        else:
            return None

    def logic_to_config(self):
        return False
    
    def config_to_logic(self):
        # if the user has pressed on Apply, we change our state
        return True

        
            
