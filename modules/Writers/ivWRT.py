# $Id: ivWRT.py,v 1.8 2005/11/04 10:35:01 cpbotha Exp $
from moduleBase import moduleBase
from moduleMixins import filenameViewModuleMixin
import moduleUtils
import vtk

class ivWRT(moduleBase, filenameViewModuleMixin):
    """ivWRT is an Inventor Viewer polygonal data writer devide module.
    """
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
        mm = self._moduleManager
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
        self.configToLogic()
        # make sure these filter through from the bottom up
        self.logicToConfig()
        self.configToView()
        
    def close(self):
        # we should disconnect all inputs
        self.setInput(0, None)
        del self._writer
        filenameViewModuleMixin.close(self)

    def getInputDescriptions(self):
	return ('vtkPolyData',)
    
    def setInput(self, idx, input_stream):
        self._writer.SetInput(input_stream)
    
    def getOutputDescriptions(self):
	return ()
    
    def getOutput(self, idx):
        raise Exception
    
    def logicToConfig(self):
        filename = self._writer.GetFileName()
        if filename == None:
            filename = ''

        self._config.filename = filename

    def configToLogic(self):
        self._writer.SetFileName(self._config.filename)

    def viewToConfig(self):
        self._config.filename = self._getViewFrameFilename()

    def configToView(self):
        self._setViewFrameFilename(self._config.filename)

    def executeModule(self):
        if len(self._writer.GetFileName()):
            self._writer.Write()

    def view(self, parent_window=None):
        # if the frame is already visible, bring it to the top; this makes
        # it easier for the user to associate a frame with a glyph
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()
