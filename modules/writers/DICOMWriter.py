# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

# Random development notes:
# * SetFileDimensionality(2) if you want multiple slices written from
#   a single volume
# * just generate im%05d.dcm filenames, as many as there are slices
# * study / series UIDs are auto generated

from moduleBase import moduleBase
from moduleMixins import \
     introspectModuleMixin
import moduleUtils
import os

import vtk
import vtkgdcm

class DICOMWriter(introspectModuleMixin, moduleBase):
    def __init__(self, module_manager):
        moduleBase.__init__(self, module_manager)

        self._writer = vtkgdcm.vtkGDCMImageWriter()

        moduleUtils.setupVTKObjectProgress(self, self._writer,
                                           'Writing DICOM data')

        self._input_data = None
        self._input_metadata = None

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

        del self._writer

        moduleBase.close(self) 

    def get_input_descriptions(self):
        return ('VTK image data', 'Medical Meta Data') 
    
    def set_input(self, idx, input_stream):
        if idx == 0:
            self._input_data = input_stream
        else:
            self._input_metadata = input_stream
    
    def get_output_descriptions(self):
        return ()
    
    def get_output(self, idx):
        raise RuntimeError

    

    def execute_module(self):
        # generate filenamelist with as many entries as there are
        # z-slices
        odir = 'c:/temp/dicomtest'

        z_len = self._input_data.GetDimensions()[2]

        fn_list = [os.path.join(odir,'im%05d.dcm' % (i,)) 
                for i in range(z_len)]
        fn_sa = vtk.vtkStringArray()
        [fn_sa.InsertNextValue(fn) for fn in fn_list]

        mip = vtk.vtkMedicalImageProperties()

        try:
            mip.DeepCopy(self._input_metadata.medical_image_properties)
        except AttributeError:
            # this simply means that we have no input metadata
            pass

        self._writer.SetMedicalImageProperties(mip)

        try:
            self._writer.SetDirectionCosines(
                    self._input_metadata.direction_cosines)
        except AttributeError:
            # we have no input metadata, set the default
            # identity matrix
            m = vtk.vtkMatrix4x4()
            self._writer.SetDirectionCosines(m)

        self._writer.SetInput(self._input_data)
        self._writer.SetFileNames(fn_sa)
        # we want to write separate slices
        self._writer.SetFileDimensionality(2)

        self._writer.Write()

    def logic_to_config(self):
        pass

    def config_to_logic(self):
        pass

    def config_to_view(self):
        pass

    def view_to_config(self):
        pass

