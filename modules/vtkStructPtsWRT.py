from module_base import module_base, filenameViewModuleMixin
from wxPython.wx import *
import vtk

class vtkStructPtsWRT(module_base, filenameViewModuleMixin):

    def __init__(self, module_manager):

        # call parent constructor
        module_base.__init__(self, module_manager)
        # ctor for this specific mixin
        filenameViewModuleMixin.__init__(self)

        self._writer = vtk.vtkStructuredPointsWriter()

        # we now have a viewFrame in self._viewFrame
        self._createViewFrame('VTK Structured Points Writer',
                              'Select a filename',
                              'VTK data (*.vtk)|*.vtk|All files (*)|*',
                              {'vtkStructuredPointsWriter': self._writer})
        
    def close(self):
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
    
    def sync_config(self):
        filename = self._writer.GetFileName()
        if filename == None:
            filename = ''

        self._setViewFrameFilename(filename)
	
    def apply_config(self):
        self._writer.SetFileName(self._getViewFrameFilename())

    def execute_module(self):
        # get the vtkPolyDataReader to try and execute
        if len(self._writer.GetFileName()):
            self._writer.Write()
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
        self._viewFrame.Show(true)
