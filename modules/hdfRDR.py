# $Id: hdfRDR.py,v 1.3 2003/02/18 14:38:33 cpbotha Exp $

from moduleBase import moduleBase
from moduleMixins import filenameViewModuleMixin
from wxPython.wx import *
from wxPython.xrc import *
import os
import vtk
import vtkdscas
import sys

class hdfRDR(moduleBase,
                  filenameViewModuleMixin):

    """dscas3 module for reading dscas HDF datasets.

    The platform makes use of HDF SDS with a custom spacing attribute.
    """
    
    def __init__(self, moduleManager):
        # call the base class __init__ (atm it just stores module_manager)
        moduleBase.__init__(self, moduleManager)
        # ctor for this specific mixin
        filenameViewModuleMixin.__init__(self)

        self._reader = vtkdscas.vtkHDFVolumeReader()

        # following is the standard way of connecting up the dscas3 progress
        # callback to a VTK object; you should do this for all objects in
        self._reader.SetProgressText('Reading HDF data')
        mm = self._moduleManager
        self._reader.SetProgressMethod(lambda s=self, mm=mm:
                                       mm.vtk_progress_cb(s._reader))
        
        # we now have a viewFrame in self._viewFrame
        self._createViewFrame('HDF Reader',
                              'Select a filename',
                              'HDF data (*.hdf)|*.hdf|All files (*)|*',
                              {'vtkHDFVolumeReader': self._reader})

        # setup defaults
        self._config.filename = ''
        
        # now get logic to agree with it
        self.configToLogic()
        # and then bring the data all the way to the top
        self.syncViewWithLogic()

        # and display the view
        self.view()

    def close(self):
        # call close of this specific mixin
        filenameViewModuleMixin.close(self)
        # take care of our binding to the reader
        del self._reader
            
    def getInputDescriptions(self):
        return ()
    
    def setInput(self, idx, input_stream):
        raise Exception
    
    def getOutputDescriptions(self):
        return (self._reader.GetOutput().GetClassName(),)

    def getOutput(self, idx):
        return self._reader.GetOutput()

    def logicToConfig(self):
        """Synchronise internal configuration information (usually
        self._config)with underlying system.
        """
        self._config.filename = self._reader.GetFileName()
        if self._config.filename is None:
            self._config.filename = ''

    def configToLogic(self):
        """Apply internal configuration information (usually self._config) to
        the underlying logic.
        """
        self._reader.SetFileName(self._config.filename)

    def viewToConfig(self):
        """Synchronise internal configuration information with the view (GUI)
        of this module.

        """
        self._config.filename = self._getViewFrameFilename()
        
    
    def configToView(self):
        """Make the view reflect the internal configuration information.

        """
        self._setViewFrameFilename(self._config.filename)
    
    def executeModule(self):
        self._reader.Update()
        # important call to make sure the app catches VTK error in the GUI
        self._moduleManager.vtk_poll_error()
            
    def view(self, parent_window=None):
        # if the window is already visible, raise it
        if not self._viewFrame.Show(true):
            self._viewFrame.Raise()
        
