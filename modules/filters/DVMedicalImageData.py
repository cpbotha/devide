# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

# to begin with, this module will take a vtkImageData,
# vtkMedicalImageProperties and a DirectionCosines (or a reader with
# GetDirectionCosines), and stuff these into a DVMedicalImageData
# object; if neither of the latter two are present, defaults will be
# used.

# eventually this module will also have a GUI with which the medical
# image properties can be easily edited.

from moduleBase import moduleBase
from moduleMixins import introspectModuleMixin
import moduleUtils
import vtk

class MedicalImageData:
    def __init__(self):
        self.image_data = None
        self.mip = vtk.vtkMedicalImageProperties()
        self.direction_cosines = None

class DVMedicalImageData(introspectModuleMixin, moduleBase):
    def __init__(self, module_manager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)

        self._input_data = None
        self._input_mip = None
        self._input_dc = None

        self._output_mid = DVMedicalImageData()

       
    def close(self):
        introspectModuleMixin.close(self)

        # we just delete our binding.  Destroying the view_frame
        # should also take care of this one.
        del self._file_dialog

        if self._view_frame is not None:
            self._view_frame.Destroy()

        del self._reader

        moduleBase.close(self) 

    def get_input_descriptions(self):
        return ('VTK image data', 'VTK medical image properties',
                'Direction Cosines')

    def set_input(self, idx, input_stream):
        if idx == 0:
            self._input_data = input_stream

        elif idx == 1:
            self._input_mip = input_stream

        else:
            self._input_dc = input_stream

    def get_output_descriptions(self):
        return ('DeVIDE Medical Image Data')

    def get_output(self, idx):
        return self._output_mid
    
    def execute_module(self):
        self._output_mid.image_data = self._input_data

        # 1. if self._input_mip is set, copy from self._input_mip to
        # self._output_mid.mip
        if not self._input_mip is None:
            self._output_mid.mip.DeepCopy(self._input_mip)
        # 2. apply only changed fields from interface
        # ... TBD

        self._output_mid.direction_cosines = self._input_dc

    def logic_to_config(self):
        pass

    def config_to_logic(self):
        pass

    def config_to_view(self):
        pass

    def view_to_config(self):
        pass

    def view(self):
        # all fields touched by user are recorded.  when we get a new
        # input, these fields are left untouched.  mmmkay?
        pass

