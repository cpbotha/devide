# $Id$

from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtk
import wx

class metaImageRDR(scriptedConfigModuleMixin, moduleBase):
    """Reads MetaImage format files.

    MetaImage files have an .mha or .mhd file extension.  .mha files are
    single files containing header and data, whereas .mhd are separate headers
    that refer to a separate raw data file.

    $Revision: 1.2 $
    """
    
    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        self._reader = vtk.vtkMetaImageReader()

        moduleUtils.setupVTKObjectProgress(self, self._reader,
                                           'Reading MetaImage data.')

        self._config.filename = ''

        configList = [
            ('File name:', 'filename', 'base:str', 'filebrowser',
             'The name of the MetaImage file you want to load.',
             {'fileMode' : wx.OPEN,
              'fileMask' :
              'MetaImage single file (*.mha)|*.mha|MetaImage separate header '
              '(*.mhd)|*.mhd|All files (*.*)|*.*'})]

        scriptedConfigModuleMixin.__init__(self, configList)

        self._viewFrame = self._createViewFrame(
            {'Module (self)' : self,
             'vtkMetaImageReader' : self._reader})

        self.configToLogic()
        self.logicToConfig()
        self.configToView()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)

        moduleBase.close(self)
        
        # get rid of our reference
        del self._reader

    def getInputDescriptions(self):
        return ()

    def setInput(self, idx, inputStream):
        raise Exception

    def getOutputDescriptions(self):
        return ('vtkImageData',)

    def getOutput(self, idx):
        return self._reader.GetOutput()

    def logicToConfig(self):
        self._config.filename = self._reader.GetFileName()

    def configToLogic(self):
        self._reader.SetFileName(self._config.filename)
        
    def executeModule(self):
        self._reader.Update()

        
        
        
