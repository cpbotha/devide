# $Id$

from module_base import ModuleBase
from moduleMixins import FilenameViewModuleMixin
import module_utils
import vtk


class vtkPolyDataWRT(FilenameViewModuleMixin, ModuleBase):

    def __init__(self, module_manager):

        # call parent constructor
        ModuleBase.__init__(self, module_manager)

        self._writer = vtk.vtkPolyDataWriter()
        # sorry about this, but the files get REALLY big if we write them
        # in ASCII - I'll make this a gui option later.
        self._writer.SetFileTypeToBinary()

        module_utils.setupVTKObjectProgress(
            self, self._writer,
            'Writing VTK Polygonal data')

        
        # ctor for this specific mixin
        FilenameViewModuleMixin.__init__(
            self,
            'Select a filename',
            'VTK data (*.vtk)|*.vtk|All files (*)|*',
            {'vtkPolyDataWriter': self._writer},
            fileOpen=False)

        # set up some defaults
        self._config.filename = ''

        self.sync_module_logic_with_config()
        
    def close(self):
        # we should disconnect all inputs
        self.set_input(0, None)
        del self._writer
        FilenameViewModuleMixin.close(self)

    def get_input_descriptions(self):
	return ('vtkStructuredPoints',)
    
    def set_input(self, idx, input_stream):
        self._writer.SetInput(input_stream)
    
    def get_output_descriptions(self):
	return ()
    
    def get_output(self, idx):
        raise Exception
    
    def logic_to_config(self):
        filename = self._writer.GetFileName()
        if filename == None:
            filename = ''

        self._config.filename = filename

    def config_to_logic(self):
        self._writer.SetFileName(self._config.filename)

    def view_to_config(self):
        self._config.filename = self._getViewFrameFilename()

    def config_to_view(self):
        self._setViewFrameFilename(self._config.filename)

    def execute_module(self):
        if len(self._writer.GetFileName()):
            self._writer.Write()
            
