# $Id: ifdocRDR.py,v 1.1 2003/08/20 13:25:43 cpbotha Exp $

from moduleBase import moduleBase
from moduleMixins import filenameViewModuleMixin
import vtk

class ifdocRDR(moduleBase, filenameViewModuleMixin):

    def __init__(self, moduleManager):
        # do the base class
        moduleBase.__init__(self, moduleManager)

        # do the mixin
        filenameViewModuleMixin.__init__(self)
        
        # setup our pipeline
        self._appendPolyData = None
        self._buildPipeline()

        # now initialise some config stuff
        self._config.dspFilename = ''

        self._createViewFrame('Select a filename',
                              'IFDOC dsp file (*.dsp)|*.dsp|All files (*)|*',
                              {'vtkAppendPolyData': self._appendPolyData})

        self.configToLogic()
        self.syncViewWithLogic()
        

    def close(self):
        pass

    def getInputDescriptions(self):
        return ()

    def setInput(self, idx, inputStream):
        raise Exception, 'This module does not accept any input.'

    def getOutputDescriptions(self):
        return ('vtkPolyData',)

    def getOutput(self, idx):
        return self._appendPolyData.GetOutput()

    def logicToConfig(self):
        """Synchronise internal configuration information (usually
        self._config)with underlying system.
        """

        pass

    def configToLogic(self):
        """Apply internal configuration information (usually self._config) to
        the underlying logic.
        """
        
        pass

    def viewToConfig(self):
        """Synchronise internal configuration information with the view (GUI)
        of this module.

        """
        self._config.dspFilename = self._getViewFrameFilename()
        
    
    def configToView(self):
        """Make the view reflect the internal configuration information.

        """
        self._setViewFrameFilename(self._config.dspFilename)
    
    def executeModule(self):
        pass
            
    def view(self, parent_window=None):
        # if the window is already visible, raise it
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()


    def _buildPipeline(self):
        # this is temporary
        self._appendPolyData = vtk.vtkAppendPolyData()

