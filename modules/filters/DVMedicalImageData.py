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

class DVMedicalImageData(introspectModuleMixin, moduleBase):
    def __init__(self, module_manager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)

        self._input_data = None
        self._input_mip = None
        self._input_dc = None

       
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
        return ()

    def get_output(self, idx):
        raise RuntimeError
    
    def execute_module(self):
        pass

    def logic_to_config(self):
        pass

    def config_to_logic(self):
        pass

    def config_to_view(self):
        pass

    def view_to_config(self):
        pass

