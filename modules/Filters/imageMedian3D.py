import genUtils
from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import moduleUtils
import wx
import vtk

class imageMedian3D(moduleBase, noConfigModuleMixin):
    
    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)
        noConfigModuleMixin.__init__(self)

        self._imageMedian3D = vtk.vtkImageMedian3D()
        self._imageMedian3D.SetKernelSize(3,3,3)
        
        moduleUtils.setupVTKObjectProgress(self, self._imageMedian3D,
                                           'Filtering with median')

        self._viewFrame = self._createViewFrame(
            {'vtkImageMedian3D' : self._imageMedian3D})

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
        noConfigModuleMixin.close(self)
        
        # get rid of our reference
        del self._imageMedian3D

    def getInputDescriptions(self):
        return ('vtkImageData',)

    def setInput(self, idx, inputStream):
        self._imageMedian3D.SetInput(inputStream)

    def getOutputDescriptions(self):
        return (self._imageMedian3D.GetOutput().GetClassName(), )

    def getOutput(self, idx):
        return self._imageMedian3D.GetOutput()

    def logicToConfig(self):
        pass
    
    def configToLogic(self):
        pass
    
    def viewToConfig(self):
        pass

    def configToView(self):
        pass
    
    def executeModule(self):
        self._imageMedian3D.Update()

    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        self._viewFrame.Show(True)
        self._viewFrame.Raise()


