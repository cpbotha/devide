# $Id$

from module_base import ModuleBase
from moduleMixins import filenameViewModuleMixin
import module_utils
import vtk


class vtkStructPtsWRT(filenameViewModuleMixin, ModuleBase):

    def __init__(self, module_manager):

        # call parent constructor
        ModuleBase.__init__(self, module_manager)

        self._writer = vtk.vtkStructuredPointsWriter()

        module_utils.setupVTKObjectProgress(
            self, self._writer,
            'Writing vtk structured points data')

        

        # we do this to save space - if you're going to be transporting files
        # to other architectures, change this to ASCII
        # we've set this back to ASCII.  Seems the binary mode is screwed
        # for some files and manages to produce corrupt files that segfault
        # VTK on Windows.
        self._writer.SetFileTypeToASCII()
        
        # ctor for this specific mixin
        filenameViewModuleMixin.__init__(
            self,
            'Select a filename',
            'VTK data (*.vtk)|*.vtk|All files (*)|*',
            {'vtkStructuredPointsWriter': self._writer},
            fileOpen=False)


        # set up some defaults
        self._config.filename = ''

        self.sync_module_logic_with_config()
        
    def close(self):
        # we should disconnect all inputs
        self.set_input(0, None)
        del self._writer
        filenameViewModuleMixin.close(self)

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
