# $Id: vtpRDR.py,v 1.1 2004/01/27 15:29:46 cpbotha Exp $

from moduleBase import moduleBase
from moduleMixins import filenameViewModuleMixin
import moduleUtils
import vtk

class vtpRDR(moduleBase, filenameViewModuleMixin):
    """Reads VTK PolyData in the VTK XML format.

    VTP is the preferred format for DeVIDE PolyData.
    """

    def __init__(self, moduleManager):

        # call parent constructor
        moduleBase.__init__(self, moduleManager)
        # ctor for this specific mixin
        filenameViewModuleMixin.__init__(self)

        self._reader = vtk.vtkXMLPolyDataReader()

        moduleUtils.setupVTKObjectProgress(
            self, self._reader,
            'Reading VTK PolyData')

        # we now have a viewFrame in self._viewFrame
        self._createViewFrame('Select a filename',
                              'VTK Poly Data (*.vtp)|*.vtp|All files (*)|*',
                              {'vtkXMLPolyDataReader': self._reader})

        # set up some defaults
        self._config.filename = ''
        self.configToLogic()
        # make sure these filter through from the bottom up
        self.syncViewWithLogic()
        
    def close(self):
        del self._reader
        filenameViewModuleMixin.close(self)

    def getInputDescriptions(self):
        return ()
    
    def setInput(self, idx, input_stream):
        raise Exception
    
    def getOutputDescriptions(self):
        return ('vtkPolyData',)
    
    def getOutput(self, idx):
        return self._reader.GetOutput()

    def logicToConfig(self):
        filename = self._reader.GetFileName()
        if filename == None:
            filename = ''

        self._config.filename = filename

    def configToLogic(self):
        self._reader.SetFileName(self._config.filename)

    def viewToConfig(self):
        self._config.filename = self._getViewFrameFilename()

    def configToView(self):
        self._setViewFrameFilename(self._config.filename)
    
    def executeModule(self):
        # get the vtkPolyDataReader to try and execute
        if len(self._reader.GetFileName()):
            self._reader.Update()

    def view(self, parent_window=None):
        self._viewFrame.Show(True)
        self._viewFrame.Raise()

