# $Id: vtkPolyDataRDR.py,v 1.5 2003/03/06 21:06:49 cpbotha Exp $

from moduleBase import moduleBase
from moduleMixins import filenameViewModuleMixin
from wxPython.wx import *
import vtk
import os

class vtkPolyDataRDR(moduleBase, filenameViewModuleMixin):
    
    def __init__(self, moduleManager):
        """Constructor (initialiser) for the PD reader.

        This is almost standard code for most of the modules making use of
        the filenameViewModuleMixin mixin.
        """
        
        # call the constructor in the "base"
        moduleBase.__init__(self, moduleManager)
        # ctor for this specific mixin
        filenameViewModuleMixin.__init__(self)

        # setup necessary VTK objects
	self._reader = vtk.vtkPolyDataReader()

        # following is the standard way of connecting up the dscas3 progress
        # callback to a VTK object; you should do this for all objects in
        self._reader.SetProgressText('Reading vtk PolyData')
        mm = self._moduleManager
        self._reader.SetProgressMethod(lambda s=self, mm=mm:
                                       mm.vtk_progress_cb(s._reader))
        
        # we now have a viewFrame in self._viewFrame
        self._createViewFrame('VTK PolyData Reader',
                              'Select a filename',
                              'VTK data (*.vtk)|*.vtk|All files (*)|*',
                              {'vtkPolyDataReader': self._reader})

        # set up some defaults
        self._config.filename = ''
        self.configToLogic()
        # make sure these filter through from the bottom up
        self.syncViewWithLogic()

        # finally we can display the GUI
        self._viewFrame.Show(1)
	
    def close(self):
        del self._reader
        # call the close method of the mixin
        filenameViewModuleMixin.close(self)

    def getInputDescriptions(self):
	return ()
    
    def setInput(self, idx, input_stream):
	raise Exception
    
    def getOutputDescriptions(self):
        # equivalent to return ('vtkPolyData',)
	return (self._reader.GetOutput().GetClassName(),)
    
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
        # get the vtkPolyDataReader to try and execute (if there's a filename)
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
        if not self._viewFrame.Show(true):
            self._viewFrame.Raise()

