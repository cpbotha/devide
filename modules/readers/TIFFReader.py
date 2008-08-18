# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

from module_base import ModuleBase
from module_mixins import ScriptedConfigModuleMixin, WX_OPEN
import module_utils
import vtk


class TIFFReader(ScriptedConfigModuleMixin, ModuleBase):
    
    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        self._reader = vtk.vtkTIFFReader()
        self._reader.SetFileDimensionality(3)

        module_utils.setup_vtk_object_progress(self, self._reader,
                                           'Reading TIFF images.')

        self._config.file_pattern = '%03d.tif'
        self._config.first_slice = 0
        self._config.last_slice = 1
        self._config.spacing = (1,1,1)
        self._config.file_lower_left = False

        configList = [
            ('File pattern:', 'file_pattern', 'base:str', 'filebrowser',
             'Filenames will be built with this.  See module help.',
             {'fileMode' : WX_OPEN,
              'fileMask' :
              'PNG files (*.png)|*.png|All files (*.*)|*.*'}),
            ('First slice:', 'first_slice', 'base:int', 'text',
             '%d will iterate starting at this number.'),
            ('Last slice:', 'last_slice', 'base:int', 'text',
             '%d will iterate and stop at this number.'),
            ('Spacing:', 'spacing', 'tuple:float,3', 'text',
             'The 3-D spacing of the resultant dataset.'),
            ('Lower left:', 'file_lower_left', 'base:bool', 'checkbox',
             'Image origin at lower left? (vs. upper left)')]

        ScriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
             'vtkTIFFReader' : self._reader})

        self.sync_module_logic_with_config()

    def close(self):
       # this will take care of all display thingies
        ScriptedConfigModuleMixin.close(self)

        ModuleBase.close(self)
        
        # get rid of our reference
        del self._reader

    def get_input_descriptions(self):
        return ()

    def set_input(self, idx, inputStream):
        raise Exception

    def get_output_descriptions(self):
        return ('vtkImageData',)

    def get_output(self, idx):
        return self._reader.GetOutput()

    def logic_to_config(self):
        self._config.file_pattern = self._reader.GetFilePattern()
        self._config.first_slice = self._reader.GetFileNameSliceOffset()
        e = self._reader.GetDataExtent()
        self._config.last_slice = self._config.first_slice + e[5] - e[4]
        self._config.spacing = self._reader.GetDataSpacing()
        self._config.file_lower_left = bool(self._reader.GetFileLowerLeft())

    def config_to_logic(self):
        self._reader.SetFilePattern(self._config.file_pattern)
        self._reader.SetFileNameSliceOffset(self._config.first_slice)
        self._reader.SetDataExtent(0,0,0,0,0,
                                   self._config.last_slice -
                                   self._config.first_slice)
        self._reader.SetDataSpacing(self._config.spacing)
        self._reader.SetFileLowerLeft(self._config.file_lower_left)

    def execute_module(self):
        self._reader.Update()

    def streaming_execute_module(self):
        self._reader.Update()
        
        
        
