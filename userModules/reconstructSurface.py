# FIXME: surfacereconstruction needs PointSet of surface points

from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import moduleUtils
from wxPython.wx import *
import vtk

class reconstructSurface(moduleBase, noConfigModuleMixin):

    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)
        # initialise any mixins we might have
        noConfigModuleMixin.__init__(self)


        # we'll be playing around with some vtk objects, this could
        # be anything
        self._geometryFilter = vtk.vtkImageDataGeometryFilter()
        self._reconstructionFilter = vtk.vtkSurfaceReconstructionFilter()
        self._mc = vtk.vtkMarchingCubes()
        self._mc.SetInput(self._reconstructionFilter.GetOutput())
        self._mc.SetValue(0, 0.0)

        moduleUtils.setupVTKObjectProgress(self, self._geometryFilter,
                                           'Extracting geometry...')
        moduleUtils.setupVTKObjectProgress(self, self._reconstructionFilter,
                                           'Reconstructing...')
        moduleUtils.setupVTKObjectProgress(self, self._mc,
                                           'Extracting surface...')

        self._iObj = self._geometryFilter
        self._oObj = self._geometryFilter
        
        self._viewFrame = self._createViewFrame({'reconstructionFilter' :
                                                 self._reconstructionFilter,
                                                 'marchingCubes' :
                                                 self._mc})


    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)
        # don't forget to call the close() method of the vtkPipeline mixin
        noConfigModuleMixin.close(self)
        # get rid of our reference
        del self._reconstructionFilter
        del self._mc
        del self._geometryFilter
        del self._iObj
        del self._oObj

    def getInputDescriptions(self):
	return ('vtkImageData',)

    def setInput(self, idx, inputStream):
        self._iObj.SetInput(inputStream)

    def getOutputDescriptions(self):
        return (self._oObj.GetOutput().GetClassName(),)

    def getOutput(self, idx):
        return self._oObj.GetOutput()

    def logicToConfig(self):
        pass

    def configToLogic(self):
        pass

    def viewToConfig(self):
        pass

    def configToView(self):
        pass

    def executeModule(self):
        self._oObj.Update()

    def view(self, parent_window=None):
        self._viewFrame.Show(True)
        self._viewFrame.Raise()
