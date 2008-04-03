# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

from moduleBase import moduleBase
from moduleMixins import \
     introspectModuleMixin
import moduleUtils

import vtkgdcm

class DICOMReader(introspectModuleMixin, moduleBase):
    def __init__(self, module_manager):
        moduleBase.__init__(self, module_manager)

        self.reader = vtkgdcm.vtkGDCMImageReader()

        moduleUtils.setupVTKObjectProgress(self, self.reader,
                                           'Reading DICOM data')

        self._view_frame = None
        self._config.dicom_filenames = []

        self.sync_module_logic_with_config()

    def close(self):
        introspectModuleMixin.close(self)
        if self._view_frame is not None:
            self._view_frame.Destroy()

        del self.reader

        moduleBase.close(self) 


    def get_input_descriptions(self):
        return ()
    
    def set_input(self, idx, input_stream):
        raise Exception
    
    def get_output_descriptions(self):
        return ('DICOM data (vtkStructuredPoints)',)
    
    def get_output(self, idx):
        return self.reader.GetOutput()

    def logic_to_config(self):
        # get filenames from reader, put in interface
        pass
        

    def config_to_logic(self):
        # add filenames to reader
        pass


    def view_to_config(self):
        # lbaat
        pass

    def config_to_view(self):
        # put list of filenames in interface
        pass

    
    def execute_module(self):
        self.reader.Update()

        if False:
            # first determine axis labels based on IOP ####################
            iop = self._reader.GetImageOrientationPatient()
            row = iop[0:3]
            col = iop[3:6]
            # the cross product (plane normal) based on the row and col will
            # also be in the RAH system (I THINK)
            norm = [0,0,0]
            vtk.vtkMath.Cross(row, col, norm)

            xl = misc_utils.major_axis_from_iop_cosine(row)
            yl = misc_utils.major_axis_from_iop_cosine(col)
            zl = misc_utils.major_axis_from_iop_cosine(norm)

            lut = {'L' : 0, 'R' : 1, 'P' : 2, 'A' : 3, 'F' : 4, 'H' : 5}

            if xl and yl and zl:
                # add this data as a vtkFieldData
                fd = self._reader.GetOutput().GetFieldData()

                axis_labels_array = vtk.vtkIntArray()
                axis_labels_array.SetName('axis_labels_array')

                for l in xl + yl + zl:
                    axis_labels_array.InsertNextValue(lut[l])

                fd.AddArray(axis_labels_array)

            # window/level ###############################################
        

    def _create_view_frame(self):


        # follow moduleBase convention to indicate that we now have
        # a view
        self.view_initialised = True
        
        

    def view(self, parent_window=None):
        if self._view_frame is None:
            self._create_view_frame()
            self.sync_module_view_with_logic()
            
        self._view_frame.Show(True)
        self._view_frame.Raise()

   
