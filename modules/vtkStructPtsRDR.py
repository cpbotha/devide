from module_base import module_base, filenameViewModuleMixin
from wxPython.wx import *
import vtk

class vtkStructPtsRDR(module_base, filenameViewModuleMixin):

    def __init__(self, module_manager):

        # call parent constructor
        module_base.__init__(self, module_manager)
        # ctor for this specific mixin
        filenameViewModuleMixin.__init__(self)

        self._reader = vtk.vtkStructuredPointsReader()

        # we now have a viewFrame in self._viewFrame
        self._createViewFrame('VTK Structured Points Reader',
                              'Select a filename',
                              'VTK data (*.vtk)|*.vtk|All files (*)|*',
                              {'vtkStructuredPointsReader': self._reader})
        
    def close(self):
        del self._reader
        filenameViewModuleMixin.close(self)

    def get_input_descriptions(self):
        return ()
    
    def set_input(self, idx, input_stream):
        raise Exception

    
    def get_output_descriptions(self):
        return ('vtkStructuredPoints',)        
    
    def get_output(self, idx):
        return self._reader.GetOutput()
    
    def sync_config(self):
        filename = self._reader.GetFileName()
        if filename == None:
            filename = ''

        self._setViewFrameFilename(filename)
	
    def apply_config(self):
        self._reader.SetFileName(self._getViewFrameFilename())

    def execute_module(self):
        # get the vtkPolyDataReader to try and execute
        if len(self._reader.GetFileName()):
            self._reader.Update()
        # tell the vtk log file window to poll the file; if the file has
        # changed, i.e. vtk has written some errors, the log window will
        # pop up.  you should do this in all your modules right after you
        # caused some VTK processing which might have resulted in VTK
        # outputting to the error log
        self._module_manager.vtk_poll_error()

    def view(self, parent_window=None):
	# first make sure that our variables agree with the stuff that
        # we're configuring
	self.sync_config()
        if not self._viewFrame.Show(true):
            self._viewFrame.Raise()

