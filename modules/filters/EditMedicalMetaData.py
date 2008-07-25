# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

from module_base import ModuleBase
from moduleMixins import introspectModuleMixin
import module_kits.vtk_kit
import moduleUtils
import vtk
import wx

from module_kits.misc_kit.devide_types import MedicalMetaData

class EditMedicalMetaData(introspectModuleMixin, ModuleBase):
    def __init__(self, module_manager):
        # initialise our base class
        ModuleBase.__init__(self, module_manager)

        self._input_mmd = None

        self._output_mmd = MedicalMetaData()
        self._output_mmd.medical_image_properties = \
                vtk.vtkMedicalImageProperties()
        self._output_mmd.direction_cosines = \
                vtk.vtkMatrix4x4()
        
        # if the value (as it appears in mk.vtk_kit.constants.mipk)
        # appears in the dict, its value refers to the user supplied
        # value.  when the user resets a field, that key is removed
        # from the dict
        self._config.new_value_dict = {}

        # this is the list of relevant properties
        self.mip_attr_l = \
            module_kits.vtk_kit.constants.medical_image_properties_keywords

        # this will be used to keep track of changes made to the prop
        # grid before they are applied to the config
        self._grid_value_dict = {}

        self._view_frame = None
        self.sync_module_logic_with_config()

       
    def close(self):
        introspectModuleMixin.close(self)

        if self._view_frame is not None:
            self._view_frame.Destroy()

        ModuleBase.close(self) 

    def get_input_descriptions(self):
        return ('Medical Meta Data',)

    def set_input(self, idx, input_stream):
        self._input_mmd = input_stream

    def get_output_descriptions(self):
        return ('Medical Meta Data',)

    def get_output(self, idx):
        return self._output_mmd
    
    def execute_module(self):
        # 1. if self._input_mmd is set, copy from self._input_mmd to
        # self._output_mmd (mmd.deep_copy checks for None)
        self._output_mmd.deep_copy(self._input_mmd)

        # 2. show input_mmd.medical_image_properties values in the
        # 'current values' column of the properties grid, only if this
        # module's view has already been shown
        self._grid_sync_with_current()

        # 3. apply only changed fields from interface
        mip = self._output_mmd.medical_image_properties
        for key,val in self._config.new_value_dict.items():
            getattr(mip, 'Set%s' % (key))(val)

    def logic_to_config(self):
        pass

    def config_to_logic(self):
        pass

    def config_to_view(self):
        if self._config.new_value_dict != self._grid_value_dict:
            self._grid_value_dict.clear()
            self._grid_value_dict.update(self._config.new_value_dict)
            # now sync grid_value_dict to actual GUI
            self._grid_sync_with_dict()

    def view_to_config(self):
        if self._config.new_value_dict == self._grid_value_dict:
            # these two are still equal, so we don't have to do
            # anything.  Return False to indicate that nothing has
            # changed.
            return False

        # transfer all values from grid_value_dict to dict in config
        self._config.new_value_dict.clear()
        self._config.new_value_dict.update(self._grid_value_dict)


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
        reload(modules.filters.resources.python.EditMedicalMetaDataViewFrame)

        self._view_frame = moduleUtils.instantiateModuleViewFrame(
            self, self._module_manager,
            modules.filters.resources.python.EditMedicalMetaDataViewFrame.\
            EditMedicalMetaDataViewFrame)


        # resize the grid and populate it with the various property
        # names
        grid = self._view_frame.prop_grid
        grid.DeleteRows(0, grid.GetNumberRows())
        grid.AppendRows(len(self.mip_attr_l))
        for i in range(len(self.mip_attr_l)):
            grid.SetCellValue(i, 0, self.mip_attr_l[i])
            # key is read-only
            grid.SetReadOnly(i, 0)
            # current value is also read-only
            grid.SetReadOnly(i, 1)
            # use special method to set new value (this also takes
            # care of cell colouring)
            self._grid_set_new_val(i, None)

        # make sure the first column fits neatly around the largest
        # key name
        grid.AutoSizeColumn(0)

        def handler_grid_cell_change(event):
            # event is a wx.GridEvent
            r,c = event.GetRow(), event.GetCol()
            grid = self._view_frame.prop_grid

            key = self.mip_attr_l[r]
            gval = grid.GetCellValue(r,c) 
            if gval == '':
                # this means the user doesn't want this field to be
                # changed, so we have to remove it from the
                # _grid_value_dict and we have to adapt the cell
                del self._grid_value_dict[key]
                # we only use this to change the cell background
                self._grid_set_new_val(r, gval, value_change=False)

            else:
                # the user has changed the value, so set it in the
                # prop dictionary
                self._grid_value_dict[key] = gval
                # and make sure the background colour is changed
                # appropriately.
                self._grid_set_new_val(r, gval, value_change=False)

        grid.Bind(wx.grid.EVT_GRID_CELL_CHANGE, handler_grid_cell_change)


        object_dict = {
                'Module (self)'      : self}

        moduleUtils.createStandardObjectAndPipelineIntrospection(
            self, self._view_frame, self._view_frame.view_frame_panel,
            object_dict, None)

        # we don't want enter to OK and escape to cancel, as these are
        # used for confirming and cancelling grid editing operations
        moduleUtils.create_eoca_buttons(self, self._view_frame,
                                        self._view_frame.view_frame_panel,
                                        ok_default=False,
                                        cancel_hotkey=False)

        # follow ModuleBase convention to indicate that we now have
        # a view
        self.view_initialised = True

        self._grid_sync_with_current()

    def _grid_set_new_val(self, row, val, value_change=True):
        grid = self._view_frame.prop_grid
        if not val is None:
            if value_change:
                # this does not trigger the CELL_CHANGE handler
                grid.SetCellValue(row, 2, val)

            grid.SetCellBackgroundColour(row, 2, wx.WHITE)

        else:
            if value_change:
                # this does not trigger the CELL_CHANGE handler
                grid.SetCellValue(row, 2, '')

            grid.SetCellBackgroundColour(row, 2, wx.LIGHT_GREY)

    def _grid_sync_with_current(self):
        """If there's an input_mmd, read out all its data and populate
        the current values column.  This method is called by the
        execute_data and also by _create_view_frame.
        """

        # we only do this if we have a view
        if not self.view_initialised:
            return

        if not self._input_mmd is None and \
                self._input_mmd.__class__ == \
                MedicalMetaData:
                    mip = self._input_mmd.medical_image_properties
                    grid = self._view_frame.prop_grid
                    for i in range(len(self.mip_attr_l)):
                        key = self.mip_attr_l[i]
                        val = getattr(mip, 'Get%s' % (key,))()
                        if val == None:
                            val = ''

                        grid.SetCellValue(i, 1, val)

    def _grid_sync_with_dict(self):
        """Synchronise property grid with _grid_value_dict ivar.
        """
        for kidx in range(len(self.mip_attr_l)):
            key = self.mip_attr_l[kidx]
            val = self._grid_value_dict.get(key,None)
            self._grid_set_new_val(kidx, val)
                
