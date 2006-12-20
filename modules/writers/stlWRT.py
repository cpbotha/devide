# $Id$
from moduleBase import moduleBase
from moduleMixins import filenameViewModuleMixin
import moduleUtils
import vtk


class stlWRT(filenameViewModuleMixin, moduleBase):

    def __init__(self, moduleManager):

        # call parent constructor
        moduleBase.__init__(self, moduleManager)

        # need to make sure that we're all happy triangles and stuff
        self._cleaner = vtk.vtkCleanPolyData()
        self._tf = vtk.vtkTriangleFilter()
        self._tf.SetInput(self._cleaner.GetOutput())
        self._writer = vtk.vtkSTLWriter()
        self._writer.SetInput(self._tf.GetOutput())
        # sorry about this, but the files get REALLY big if we write them
        # in ASCII - I'll make this a gui option later.
        #self._writer.SetFileTypeToBinary()

        # following is the standard way of connecting up the devide progress
        # callback to a VTK object; you should do this for all objects in
        mm = self._moduleManager        
        for textobj in (('Cleaning data', self._cleaner),
                        ('Converting to triangles', self._tf),
                        ('Writing STL data', self._writer)):
            moduleUtils.setupVTKObjectProgress(self, textobj[1],
                                               textobj[0])

            
        # ctor for this specific mixin
        filenameViewModuleMixin.__init__(
            self,
            'Select a filename',
            'STL data (*.stl)|*.stl|All files (*)|*',
            {'vtkSTLWriter': self._writer},
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
	return ('vtkPolyData',)
    
    def set_input(self, idx, input_stream):
        self._cleaner.SetInput(input_stream)
    
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
