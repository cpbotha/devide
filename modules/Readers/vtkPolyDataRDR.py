# $Id: vtkPolyDataRDR.py,v 1.2 2003/09/23 14:53:48 cpbotha Exp $

from moduleBase import moduleBase
from moduleMixins import filenameViewModuleMixin
import moduleUtils
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

        moduleUtils.setupVTKObjectProgress(
            self, self._reader,
            'Reading vtk polydata')

#         def errorEventCallback(o, e, msg):
#             print msg

#         errorEventCallback.callDataType = 'string0'
            
#         self._reader.AddObserver('ErrorEvent', errorEventCallback)
        
        # we now have a viewFrame in self._viewFrame
        self._createViewFrame('Select a filename',
                              'VTK data (*.vtk)|*.vtk|All files (*)|*',
                              {'vtkPolyDataReader': self._reader})

        # set up some defaults
        self._config.filename = ''
        self.configToLogic()
        # make sure these filter through from the bottom up
        self.syncViewWithLogic()

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
            
    def view(self, parent_window=None):
        # if the frame is already visible, bring it to the top; this makes
        # it easier for the user to associate a frame with a glyph
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()

        print "blaat"
        print moduleBase
        print "blaat 2"
        
