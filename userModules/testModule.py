from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import moduleUtils
from wxPython.wx import *
import vtk

class testModule(moduleBase, noConfigModuleMixin):

    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)
        # initialise any mixins we might have
        noConfigModuleMixin.__init__(self)


        # we'll be playing around with some vtk objects, this could
        # be anything
        self._triangleFilter = vtk.vtkTriangleFilter()
        self._curvatures = vtk.vtkCurvatures()
        self._curvatures.SetCurvatureTypeToGaussian()
        self._curvatures.SetInput(self._triangleFilter.GetOutput())

        moduleUtils.setupVTKObjectProgress(self, self._triangleFilter,
                                           'Triangle filtering...')
        moduleUtils.setupVTKObjectProgress(self, self._curvatures,
                                           'Calculating curvatures...')
        
        
        self._viewFrame = self._createViewFrame({'triangleFilter' :
                                                 self._triangleFilter,
                                                 'curvatures' :
                                                 self._curvatures})

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)
        # don't forget to call the close() method of the vtkPipeline mixin
        noConfigModuleMixin.close(self)
        # get rid of our reference
        del self._triangleFilter
        del self._curvatures

    def getInputDescriptions(self):
	return ('vtkPolyData',)

    def setInput(self, idx, inputStream):
        self._triangleFilter.SetInput(inputStream)

    def getOutputDescriptions(self):
        return (self._curvatures.GetOutput().GetClassName(),)

    def getOutput(self, idx):
        return self._curvatures.GetOutput()

    def logicToConfig(self):
        pass

    def configToLogic(self):
        pass

    def viewToConfig(self):
        pass

    def configToView(self):
        pass

    def executeModule(self):
        self._curvatures.Update()

    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()
