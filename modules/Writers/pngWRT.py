# $Id: pngWRT.py,v 1.1 2004/03/30 11:07:35 cpbotha Exp $

from moduleBase import moduleBase
from moduleMixins import filenameViewModuleMixin
import moduleUtils
import wx
import vtk

class pngWRT(moduleBase, filenameViewModuleMixin):
    """Writes a single PNG image to disk.

    TODO: add series writing.

    $Revision: 1.1 $
    """

    def __init__(self, moduleManager):

        # call parent constructor
        moduleBase.__init__(self, moduleManager)
        # ctor for this specific mixin
        filenameViewModuleMixin.__init__(self)

        self._shiftScale = vtk.vtkImageShiftScale()
        self._shiftScale.SetOutputScalarTypeToUnsignedChar()
        self._writer = vtk.vtkPNGWriter()
        self._writer.SetInput(self._shiftScale.GetOutput())

        moduleUtils.setupVTKObjectProgress(
            self, self._writer,
            'Writing PNG file(s)')

        # we now have a viewFrame in self._viewFrame
        self._createViewFrame('Select a filename',
                              'PNG files (*.png)|*.png|All files (*)|*',
                              {'vtkPNGWriter': self._writer})

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
	return ('vtkImageData',)
    
    def setInput(self, idx, input_stream):
        self._shiftScale.SetInput(input_stream)
    
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
        if len(self._writer.GetFileName()) and self._shiftScale.GetInput():
            inp = self._shiftScale.GetInput()
            inp.Update()
            minv,maxv = inp.GetScalarRange()
            self._shiftScale.SetShift(-minv)
            self._shiftScale.SetScale(255 / (maxv - minv))
            self._writer.Write()

    def view(self, parent_window=None):
        self._viewFrame.Show(True)
        self._viewFrame.Raise()
