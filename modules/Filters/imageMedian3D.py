import genUtils
from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import wx
import vtk

class imageMedian3D(scriptedConfigModuleMixin, moduleBase):
    """Performs 3D morphological median on input data.
    
    $Revision: 1.2 $
    """
    
    
    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)

        self._config.kernelSize = (3, 3, 3)

        configList = [
            ('Kernel size:', 'kernelSize', 'tuple:int,3', 'text',
             'Size of structuring element in pixels.')]

        scriptedConfigModuleMixin.__init__(self, configList)

        self._imageMedian3D = vtk.vtkImageMedian3D()
        
        moduleUtils.setupVTKObjectProgress(self, self._imageMedian3D,
                                           'Filtering with median')

        self._createWindow(
            {'Module (self)' : self,
             'vtkImageMedian3D' : self._imageMedian3D})

        # pass the data down to the underlying logic
        self.configToLogic()
        # and all the way up from logic -> config -> view to make sure
        self.syncViewWithLogic()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)
        
        # get rid of our reference
        del self._imageMedian3D

    def executeModule(self):
        self._imageMedian3D.Update()

    def getInputDescriptions(self):
        return ('vtkImageData',)

    def setInput(self, idx, inputStream):
        self._imageMedian3D.SetInput(inputStream)

    def getOutputDescriptions(self):
        return (self._imageMedian3D.GetOutput().GetClassName(), )

    def getOutput(self, idx):
        return self._imageMedian3D.GetOutput()

    def logicToConfig(self):
        self._config.kernelSize = self._imageMedian3D.GetKernelSize()
    
    def configToLogic(self):
        ks = self._config.kernelSize
        self._imageMedian3D.SetKernelSize(ks[0], ks[1], ks[2])

    

