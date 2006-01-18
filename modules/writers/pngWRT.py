# $Id$

from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtk
import wx

class pngWRT(scriptedConfigModuleMixin, moduleBase):
    """Writes a volume as a series of PNG images.

    Set the file pattern by making use of the file browsing dialog.  Replace
    the increasing index by a %d format specifier.  %3d can be used for
    example, in which case %d will be replaced by an integer zero padded to 3
    digits, i.e. 000, 001, 002 etc.  %d starts from 0.

    Module by Joris van Zwieten.

    $Revision: 1.3 $
    """

    def __init__(self, moduleManager):

        # call parent constructor
        moduleBase.__init__(self, moduleManager)
        # ctor for this specific mixin
        # filenameViewModuleMixin.__init__(self)
	
	self._shiftScale = vtk.vtkImageShiftScale()
        self._shiftScale.SetOutputScalarTypeToUnsignedShort()
	
	self._writer = vtk.vtkPNGWriter()
	self._writer.SetFileDimensionality(3)
        self._writer.SetInput(self._shiftScale.GetOutput())
        
	moduleUtils.setupVTKObjectProgress(self, self._writer, 'Writing PNG file(s)')
       
        self._config.filePattern = '%d.png'

        configList = [
            ('File pattern:', 'filePattern', 'base:str', 'filebrowser',
             'Filenames will be built with this.  See module help.',
             {'fileMode' : wx.OPEN,
              'fileMask' :
              'PNG files (*.png)|*.png|All files (*.*)|*.*'})]

        scriptedConfigModuleMixin.__init__(self, configList)

        self._viewFrame = self._createViewFrame(
            {'Module (self)' : self,
             'vtkPNGWriter' : self._writer})

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
        del self._writer


    def getInputDescriptions(self):
	return ('vtkImageData',)
    
    def setInput(self, idx, input_stream):
        self._shiftScale.SetInput(input_stream)
    
    def getOutputDescriptions(self):
	return ()
    
    def getOutput(self, idx):
       	raise Exception

    def logicToConfig(self):
        self._config.filePattern = self._writer.GetFilePattern()

    def configToLogic(self):
        self._writer.SetFilePattern(self._config.filePattern)
    
    def executeModule(self):
        if len(self._writer.GetFilePattern()) and self._shiftScale.GetInput():
            inp = self._shiftScale.GetInput()
            inp.Update()
            minv,maxv = inp.GetScalarRange()
            self._shiftScale.SetShift(-minv)
            self._shiftScale.SetScale(65535 / (maxv - minv))
	    self._writer.Write()
            self._moduleManager.setProgress(
                100.0, "vtkPNGWriter: Writing PNG file(s). [DONE]")

