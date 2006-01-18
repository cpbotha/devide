# $Id$

from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtk
import wx

class pngRDR(scriptedConfigModuleMixin, moduleBase):
    """Reads a series of PNG files.

    Set the file pattern by making use of the file browsing dialog.  Replace
    the increasing index by a %d format specifier.  %3d can be used for
    example, in which case %d will be replaced by an integer zero padded to 3
    digits, i.e. 000, 001, 002 etc.  %d counts from the 'First slice' to the
    'Last slice'.

    $Revision: 1.4 $
    """
    
    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        self._reader = vtk.vtkPNGReader()
        self._reader.SetFileDimensionality(3)

        moduleUtils.setupVTKObjectProgress(self, self._reader,
                                           'Reading PNG images.')

        self._config.filePattern = '%03d.png'
        self._config.firstSlice = 0
        self._config.lastSlice = 1
        self._config.spacing = (1,1,1)
        self._config.fileLowerLeft = False

        configList = [
            ('File pattern:', 'filePattern', 'base:str', 'filebrowser',
             'Filenames will be built with this.  See module help.',
             {'fileMode' : wx.OPEN,
              'fileMask' :
              'PNG files (*.png)|*.png|All files (*.*)|*.*'}),
            ('First slice:', 'firstSlice', 'base:int', 'text',
             '%d will iterate starting at this number.'),
            ('Last slice:', 'lastSlice', 'base:int', 'text',
             '%d will iterate and stop at this number.'),
            ('Spacing:', 'spacing', 'tuple:float,3', 'text',
             'The 3-D spacing of the resultant dataset.'),
            ('Lower left:', 'fileLowerLeft', 'base:bool', 'checkbox',
             'Image origin at lower left? (vs. upper left)')]

        scriptedConfigModuleMixin.__init__(self, configList)

        self._viewFrame = self._createViewFrame(
            {'Module (self)' : self,
             'vtkPNGReader' : self._reader})

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
        #self._config.filePrefix = self._reader.GetFilePrefix()
        self._config.filePattern = self._reader.GetFilePattern()
        self._config.firstSlice = self._reader.GetFileNameSliceOffset()
        e = self._reader.GetDataExtent()
        self._config.lastSlice = self._config.firstSlice + e[5] - e[4]
        self._config.spacing = self._reader.GetDataSpacing()
        self._config.fileLowerLeft = bool(self._reader.GetFileLowerLeft())

    def configToLogic(self):
        #self._reader.SetFilePrefix(self._config.filePrefix)
        self._reader.SetFilePattern(self._config.filePattern)
        self._reader.SetFileNameSliceOffset(self._config.firstSlice)
        self._reader.SetDataExtent(0,0,0,0,0,
                                   self._config.lastSlice -
                                   self._config.firstSlice)
        self._reader.SetDataSpacing(self._config.spacing)
        self._reader.SetFileLowerLeft(self._config.fileLowerLeft)

    def executeModule(self):
        self._reader.Update()

        
        
        
