# $Id$
from moduleBase import moduleBase
from moduleMixins import filenameViewModuleMixin
import moduleUtils
import vtk


class ivWRT(moduleBase, filenameViewModuleMixin):
    def __init__(self, moduleManager):

        # call parent constructor
        moduleBase.__init__(self, moduleManager)
        # ctor for this specific mixin
        filenameViewModuleMixin.__init__(self)

        self._writer = vtk.vtkIVWriter()
        # sorry about this, but the files get REALLY big if we write them
        # in ASCII - I'll make this a gui option later.
        #self._writer.SetFileTypeToBinary()

        # following is the standard way of connecting up the devide progress
        # callback to a VTK object; you should do this for all objects in
        moduleUtils.setupVTKObjectProgress(
            self, self._writer, 'Writing polydata to Inventor Viewer format')

        
        
        # we now have a viewFrame in self._viewFrame
        self._createViewFrame(
            'Select a filename',
            'InventorViewer data (*.iv)|*.iv|All files (*)|*',
            {'vtkIVWriter': self._writer},
            fileOpen=False)

        # set up some defaults
        self._config.filename = ''
        self.config_to_logic()
        # make sure these filter through from the bottom up
        self.logic_to_config()
        self.config_to_view()
        
    def close(self):
        # we should disconnect all inputs
        self.set_input(0, None)
        del self._writer
        filenameViewModuleMixin.close(self)

    def get_input_descriptions(self):
	return ('vtkPolyData',)
    
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

        

    def view(self, parent_window=None):
        # if the frame is already visible, bring it to the top; this makes
        # it easier for the user to associate a frame with a glyph
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()
