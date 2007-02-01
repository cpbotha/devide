# $Id$

from moduleBase import moduleBase
from moduleMixins import filenameViewModuleMixin
import moduleUtils
import vtk


class vtiRDR(filenameViewModuleMixin, moduleBase):

    def __init__(self, moduleManager):

        # call parent constructor
        moduleBase.__init__(self, moduleManager)

        self._reader = vtk.vtkXMLImageDataReader()
        
        # ctor for this specific mixin
        filenameViewModuleMixin.__init__(
            self,
            'Select a filename',
            'VTK Image Data (*.vti)|*.vti|All files (*)|*',
            {'vtkXMLImageDataReader': self._reader,
             'Module (self)' : self})

        moduleUtils.setupVTKObjectProgress(
            self, self._reader,
            'Reading VTK ImageData')

        # set up some defaults
        self._config.filename = ''

        # there is no view yet...
        self._moduleManager.sync_module_logic_with_config(self)
        
    def close(self):
        del self._reader
        filenameViewModuleMixin.close(self)

    def get_input_descriptions(self):
        return ()
    
    def set_input(self, idx, input_stream):
        raise Exception
    
    def get_output_descriptions(self):
        return ('vtkImageData',)
    
    def get_output(self, idx):
        return self._reader.GetOutput()

    def logic_to_config(self):
        filename = self._reader.GetFileName()
        if filename == None:
            filename = ''

        self._config.filename = filename

    def config_to_logic(self):
        self._reader.SetFileName(self._config.filename)

    def view_to_config(self):
        self._config.filename = self._getViewFrameFilename()

    def config_to_view(self):
        self._setViewFrameFilename(self._config.filename)
    
    def execute_module(self):
        # get the vtkPolyDataReader to try and execute
        if len(self._reader.GetFileName()):
            self._reader.Update()
            

