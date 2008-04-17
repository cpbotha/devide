# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

# Random development notes:
# * SetFileDimensionality(2) if you want multiple slices written from
#   a single volume
# * just generate im%05d.dcm filenames, as many as there are slices
# * where do we get DirectionCosines from? (not in
#   vtkMedicalImageProperties)
# * study / series UIDs are auto generated

from moduleBase import moduleBase
from moduleMixins import \
     introspectModuleMixin
import moduleUtils

import vtkgdcm

class DICOMWriter(introspectModuleMixin, moduleBase):
    def __init__(self, module_manager):
        moduleBase.__init__(self, module_manager)

        self._writer = vtkgdcm.vtkGDCMImageWriter()

        moduleUtils.setupVTKObjectProgress(self, self._reader,
                                           'Writing DICOM data')

        self._view_frame = None
        self._file_dialog = None
        self._config.dicom_filenames = []

        self.sync_module_logic_with_config()

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
        return ()
    
    def set_input(self, idx, input_stream):
        raise Exception
    
    def get_output_descriptions(self):
        return ('DICOM data (vtkStructuredPoints)',)
    
    def get_output(self, idx):
        return self._reader.GetOutput()

