# $Id: vtkPolyDataWRT.py,v 1.1 2003/03/13 17:20:25 cpbotha Exp $

from moduleBase import moduleBase
from moduleMixins import filenameViewModuleMixin
from wxPython.wx import *
import vtk

class vtkPolyDataWRT(moduleBase, filenameViewModuleMixin):

    def __init__(self, moduleManager):

        # call parent constructor
        moduleBase.__init__(self, moduleManager)
        # ctor for this specific mixin
        filenameViewModuleMixin.__init__(self)

        self._writer = vtk.vtkPolyDataWriter()

        # following is the standard way of connecting up the dscas3 progress
        # callback to a VTK object; you should do this for all objects in
        self._writer.SetProgressText('Writing VTK Polygonal data')
        mm = self._moduleManager
        self._writer.SetProgressMethod(lambda s=self, mm=mm:
                                       mm.vtk_progress_cb(s._writer))
        
        # we do this to save space - if you're going to be transporting files
        # to other architectures, change this to ASCII
        #self._writer.SetFileTypeToBinary()

        # we now have a viewFrame in self._viewFrame
        self._createViewFrame('VTK PolyData Writer',
                              'Select a filename',
                              'VTK data (*.vtk)|*.vtk|All files (*)|*',
                              {'vtkPolyDataWriter': self._writer})

        # set up some defaults
        self._config.filename = ''
        self.configToLogic()
        # make sure these filter through from the bottom up
        self.syncViewWithLogic()

        # finally we can display the GUI
        self._viewFrame.Show(1)
        
    def close(self):
        # we should disconnect all inputs
        self.setInput(0, None)
        del self._writer
        filenameViewModuleMixin.close(self)

    def getInputDescriptions(self):
	return ('vtkStructuredPoints',)
    
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
