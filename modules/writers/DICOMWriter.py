# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

# Random development notes:
# * SetFileDimensionality(2) if you want multiple slices written from
#   a single volume
# * just generate im%05d.dcm filenames, as many as there are slices
# * study / series UIDs are auto generated

from module_base import ModuleBase
from moduleMixins import \
     scriptedConfigModuleMixin
import moduleUtils
import os

import vtk
import vtkgdcm
import wx # need this for wx.SAVE

RADIOBOX_IDX, DIR_IDX, FILE_IDX = 0, 1, 2

class DICOMWriter(scriptedConfigModuleMixin, ModuleBase):
    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        self._writer = vtkgdcm.vtkGDCMImageWriter()
        moduleUtils.setupVTKObjectProgress(self, self._writer,
                                           'Writing DICOM data')

        self._caster = vtk.vtkImageCast()
        self._caster.SetOutputScalarTypeToShort()
        moduleUtils.setupVTKObjectProgress(self, self._caster,
                'Casting DICOM data to short')

        self._input_data = None
        self._input_metadata = None

        self._config.output_mode = 0
        self._config.output_directory = ''
        self._config.output_filename = ''
        self._config.cast_to_short = True

        config_list = [
                ('Output mode:', 'output_mode', 'base:int',
                    'radiobox', 'Output mode',
                    ['Slice-per-file (directory)', 
                     'Multi-slice per file (file)']),
                ('Output directory:', 'output_directory', 'base:str',
                'dirbrowser', 
                'Directory that takes slice-per-file output'),
                ('Output filename:', 'output_filename', 'base:str',
                 'filebrowser', 
                 'Output filename for multi-slice per file output.',
                 {'fileMode' : wx.SAVE,
                     'fileMask' : 'DICOM file (*.dcm)|*.dcm|'
                     'All files (*.*)|*.*'}
                 ),
                ('Cast to short:', 'cast_to_short', 'base:bool',
                    'checkbox',
                    'Should the data be cast to signed 16-bit (short), '
                    'common for DICOM.')
                ]

        scriptedConfigModuleMixin.__init__(self, config_list,
                {'Module (self)' : self})


        self.sync_module_logic_with_config()


    def close(self):
        scriptedConfigModuleMixin.close(self)
        ModuleBase.close(self) 

        del self._writer

    def get_input_descriptions(self):
        return ('VTK image data', 'Medical Meta Data') 
    
    def set_input(self, idx, input_stream):
        if idx == 0:
            self._input_data = input_stream

            if input_stream is None:
                # we explicitly disconnect our filters too
                self._caster.SetInput(None)
                self._writer.SetInput(None)

        else:
            self._input_metadata = input_stream
    
    def get_output_descriptions(self):
        return ()
    
    def get_output(self, idx):
        raise RuntimeError

    def execute_module(self):
        if self._config.output_mode == 0:
            # slice-per-file mode

            if not os.path.isdir(self._config.output_directory):
                raise RuntimeError(
                        'Please specify a valid output directory.')

            # generate filenamelist with as many entries as there are
            # z-slices
            self._input_data.UpdateInformation() # shouldn't be nec.
            z_len = self._input_data.GetDimensions()[2]
            odir = self._config.output_directory
            fn_list = [os.path.join(odir,'im%05d.dcm' % (i,)) 
                       for i in range(1, z_len+1)]

            fn_sa = vtk.vtkStringArray()
            [fn_sa.InsertNextValue(fn) for fn in fn_list]
            self._writer.SetFileNames(fn_sa)
            self._writer.SetFileDimensionality(2)

        else: # output_mode == 1, multi-slices per file
            if not self._config.output_filename:
                raise RuntimeError(
                        'Please specify an output filename.')

            self._writer.SetFileName(self._config.output_filename)
            self._writer.SetFileDimensionality(3)

        # now setup the common stuff
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

        if self._config.cast_to_short:
            self._caster.SetInput(self._input_data)
            # if we don't call this update, it crashes on Windows with
            # GDCM 2.0.5, and everything else shortly before DeVIDE
            # 8.5.  The crash is inside the vtkGDCMImageWriter.
            self._caster.Update()
            self._writer.SetInput(self._caster.GetOutput())
        else:
            # just to be sure
            self._caster.SetInput(None)
            self._writer.SetInput(self._input_data)

        self._writer.Write()

    def logic_to_config(self):
        pass

    def config_to_logic(self):
        pass

    def view(self):
        # call to our parent
        scriptedConfigModuleMixin.view(self)

        # get binding to radiobox
        radiobox = self._getWidget(RADIOBOX_IDX)
        # bind change event to it
        radiobox.Bind(wx.EVT_RADIOBOX, self._handler_output_mode_radiobox)
        # make sure the initial state is ok
        self._toggle_filedir(radiobox.GetSelection())


    def _handler_output_mode_radiobox(self, event):
        self._toggle_filedir(event.GetEventObject().GetSelection())

    def _toggle_filedir(self, idx):
        dir_widget = self._getWidget(DIR_IDX)
        file_widget = self._getWidget(FILE_IDX)
        if idx == 0:
            # user wants slice-per-file, so we enable dir widget
            dir_widget.Enable()
            file_widget.Disable()
        else:
            dir_widget.Disable()
            file_widget.Enable()


