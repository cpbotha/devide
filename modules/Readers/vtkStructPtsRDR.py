# $Id: vtkStructPtsRDR.py,v 1.1 2003/09/20 21:23:51 cpbotha Exp $

from moduleBase import moduleBase
from moduleMixins import filenameViewModuleMixin
import moduleUtils
from wxPython.wx import *
import vtk

class vtkStructPtsRDR(moduleBase, filenameViewModuleMixin):

    def __init__(self, moduleManager):

        # call parent constructor
        moduleBase.__init__(self, moduleManager)
        # ctor for this specific mixin
        filenameViewModuleMixin.__init__(self)

        self._reader = vtk.vtkStructuredPointsReader()

        moduleUtils.setupVTKObjectProgress(
            self, self._reader,
            'Reading vtk structured points data')

        # we now have a viewFrame in self._viewFrame
        self._createViewFrame('Select a filename',
                              'VTK data (*.vtk)|*.vtk|All files (*)|*',
                              {'vtkStructuredPointsReader': self._reader})

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
        return ('vtkStructuredPoints',)
    
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
        # tell the vtk log file window to poll the file; if the file has
        # changed, i.e. vtk has written some errors, the log window will
        # pop up.  you should do this in all your modules right after you
        # caused some VTK processing which might have resulted in VTK
        # outputting to the error log
        self._moduleManager.vtk_poll_error()

    def view(self, parent_window=None):
        # if the frame is already visible, bring it to the top; this makes
        # it easier for the user to associate a frame with a glyph
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()

