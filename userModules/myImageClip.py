from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtk
import wx

class myImageClip(scriptedConfigModuleMixin, moduleBase):
    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        self._clipper = vtk.vtkImageClip()

        moduleUtils.setupVTKObjectProgress(self, self._clipper,
                                           'Reading PNG images.')

        self._config.outputWholeExtent = (0,-1,0,-1,0,-1)

        configList = [
            ('OutputWholeExtent:', 'outputWholeExtent', 'tuple:float,6', 'text',
             'The size of the clip volume.')]

        scriptedConfigModuleMixin.__init__(self, configList)

        self._viewFrame = self._createViewFrame(
            {'Module (self)' : self,
             'vtkImageClip' : self._clipper})

        self.configToLogic()
        self.syncViewWithLogic()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)
        moduleBase.close(self)
        
        # get rid of our reference
        del self._clipper

    def getInputDescriptions(self):
        return ('vtkImageData',)

    def setInput(self, idx, inputStream):
        if idx == 0:
            self._clipper.SetInput(inputStream)
        else:
            raise Exception

    def getOutputDescriptions(self):
        return ('vtkImageData',)

    def getOutput(self, idx):
        return self._clipper.GetOutput()

    def logicToConfig(self):
        self._config.outputWholeExtent = self._clipper.GetOutputWholeExtent()

    def configToLogic(self):
        self._clipper.SetOutputWholeExtent( self._config.outputWholeExtent, None )

    def executeModule(self):
        self._clipper.Update()
        