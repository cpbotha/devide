# ifdocVWR copyright (c) 2003 by Charl P. Botha cpbotha@ieee.org
# $Id: ifdocVWR.py,v 1.2 2003/08/29 16:45:56 cpbotha Exp $
# module to interact with the ifdoc shoulder model

from moduleBase import moduleBase

class ifdocVWR(moduleBase):

    def __init__(self, moduleManager):
        # base constructor
        moduleBase.__init__(self, moduleManager)

    def close(self):
        pass

    def getInputDescriptions(self):
        return ('IFDOC M file',)

    def setInput(self, idx, inputStream):
        # don't forget to register as an observer
        self.mData = inputStream

    def getOutputDescriptions(self):
        return ()

    def getOutput(self, idx):
        raise Exception

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
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()
    
    
