# $Id: vtk_hdf_rdr.py,v 1.22 2003/01/28 22:38:34 cpbotha Exp $

from moduleBase import moduleBase
from moduleMixins import filenameViewModuleMixin
from wxPython.wx import *
from wxPython.xrc import *
import os
import vtk
import vtkdscas
import module_utils
import sys

class vtk_hdf_rdr(moduleBase,
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

        # we now have a viewFrame in self._viewFrame
        self._createViewFrame('HDF Reader',
                              'Select a filename',
                              'HDF data (*.hdf)|*.hdf|All files (*)|*',
                              {'vtkHDFVolumeReader': self._reader})
        

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
        # following is the standard way of connecting up the dscas3 progress
        # callback to a VTK object; you should do this for all objects in
        # your module - you could do this in __init__ as well, it seems
        # neater here though
        self._reader.SetProgressText('Reading HDF data')
        mm = self._moduleManager
        self._reader.SetProgressMethod(lambda s=self, mm=mm:
                                       mm.vtk_progress_cb(s._reader))
        
        self._reader.Update()
        # important call to make sure the app catches VTK error in the GUI
        self._moduleManager.vtk_poll_error()

        mm.setProgress(100, 'DONE reading HDF data')
            
    def view(self, parent_window=None):
        # first make sure that our variables agree with the stuff that
        # we're configuring
        self.syncViewWithLogic()
        self._viewFrame.Show(true)
        
