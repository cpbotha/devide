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

from module_kits.misc_kit.devide_types import MedicalMetaData

class MedicalImageData:
    def __init__(self):
        self.image_data = None
        self.mip = vtk.vtkMedicalImageProperties()
        self.direction_cosines = None

class EditMedicalMetaData(introspectModuleMixin, moduleBase):
    def __init__(self, module_manager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)

        self._input_mmd = None

        self._output_mmd = MedicalMetaData()
        self._output_mmd.medical_image_properties = \
                vtk.vtkMedicalImageProperties()
        self._output_mmd.direction_cosines = \
                vtk.vtkMatrix4x4()

        self._view_frame = None
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
        return ('Medical Meta Data',)

    def set_input(self, idx, input_stream):
        self._input_mmd = input_stream

    def get_output_descriptions(self):
        return ('Medical Meta Data')

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

        if self._view_frame is None:
            self._create_view_frame()
            self.sync_module_view_with_logic()
            
        self._view_frame.Show(True)
        self._view_frame.Raise()

    def _create_view_frame(self):
        import modules.filters.resources.python.EditMedicalMetaDataViewFrame
        reload(modules.readers.resources.python.EditMedicalMetaDataViewFrame)

        self._view_frame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager,
            modules.readers.resources.python.EditMedicalMetaDataViewFrame.\
            EditMedicalMetaDataViewFrame)


        object_dict = {
                'Module (self)'      : self}
        moduleUtils.createStandardObjectAndPipelineIntrospection(
            self, self._view_frame, self._view_frame.view_frame_panel,
            object_dict, None)

        moduleUtils.createECASButtons(self, self._view_frame,
                                      self._view_frame.view_frame_panel)

        # now add the event handlers
        #self._view_frame.add_files_b.Bind(wx.EVT_BUTTON,
        #        self._handler_add_files_b)
        #self._view_frame.remove_files_b.Bind(wx.EVT_BUTTON,
        #        self._handler_remove_files_b)

        # follow moduleBase convention to indicate that we now have
        # a view
        self.view_initialised = True

