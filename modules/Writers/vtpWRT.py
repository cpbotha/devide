# $Id: vtpWRT.py,v 1.2 2005/06/27 09:30:44 cpbotha Exp $

from moduleBase import moduleBase
from moduleMixins import filenameViewModuleMixin
import moduleUtils
import wx
import vtk

class vtpWRT(moduleBase, filenameViewModuleMixin):
    """Writes VTK PolyData in the VTK XML format.  The data attribute is
    compressed.

    This is the preferred way of saving PolyData in DeVIDE.
    """

    def __init__(self, moduleManager):

        # call parent constructor
        moduleBase.__init__(self, moduleManager)
        # ctor for this specific mixin
        filenameViewModuleMixin.__init__(self)

        self._writer = vtk.vtkXMLPolyDataWriter()

        moduleUtils.setupVTKObjectProgress(
            self, self._writer,
            'Writing VTK PolyData')

        self._writer.SetDataModeToBinary()

        # we now have a viewFrame in self._viewFrame
        self._createViewFrame('Select a filename',
                              'VTK PolyData (*.vtp)|*.vtp|All files (*)|*',
                              {'vtkXMLPolyDataWriter': self._writer},
                              fileOpen=False)

        # set up some defaults
        self._config.filename = ''
        self.configToLogic()
        # make sure these filter through from the bottom up
        self.syncViewWithLogic()

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
        self._viewFrame.Show(True)
        self._viewFrame.Raise()
