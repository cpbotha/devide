import genUtils
from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import moduleUtils
import wx
import vtk

class clipPolyData(moduleBase, noConfigModuleMixin):
    """Given an input polydata and an implicitFunction, this will clip
    the polydata.
    """
    
    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)
        noConfigModuleMixin.__init__(self)

        self._clipPolyData = vtk.vtkClipPolyData()
        moduleUtils.setupVTKObjectProgress(self, self._clipPolyData,
                                           'Calculating normals')

        self._viewFrame = self._createViewFrame(
            {'vtkClipPolyData' : self._clipPolyData})

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
        del self._pdNormals

    def getInputDescriptions(self):
        return ('vtkPolyData',)

    def setInput(self, idx, inputStream):
        self._pdNormals.SetInput(inputStream)

    def getOutputDescriptions(self):
        return (self._pdNormals.GetOutput().GetClassName(), )

    def getOutput(self, idx):
        return self._pdNormals.GetOutput()

    def logicToConfig(self):
        pass
    
    def configToLogic(self):
        pass
    
    def viewToConfig(self):
        pass

    def configToView(self):
        pass
    
    def executeModule(self):
        self._pdNormals.Update()

    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()

