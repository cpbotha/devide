from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import moduleUtils
import vtk

class reconstructSurface(moduleBase, noConfigModuleMixin):
    """Given a binary volume, fit a surface through the marked points.

    A doubleThreshold could be used to extract points of interest from
    a volume.  By passing it through this module, a surface will be
    fit through those points of interest.  The points of interest have
    to be of value 1 or greater.

    This is not to be confused with traditional iso-surface extraction.
    """
    

    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)
        # initialise any mixins we might have
        noConfigModuleMixin.__init__(self)


        # we'll be playing around with some vtk objects, this could
        # be anything
        self._thresh = vtk.vtkThresholdPoints()
        # this is wacked syntax!
        self._thresh.ThresholdByUpper(1)
        self._reconstructionFilter = vtk.vtkSurfaceReconstructionFilter()
        self._reconstructionFilter.SetInput(self._thresh.GetOutput())
        self._mc = vtk.vtkMarchingCubes()
        self._mc.SetInput(self._reconstructionFilter.GetOutput())
        self._mc.SetValue(0, 0.0)

        moduleUtils.setupVTKObjectProgress(self, self._thresh,
                                           'Extracting points...')
        moduleUtils.setupVTKObjectProgress(self, self._reconstructionFilter,
                                           'Reconstructing...')
        moduleUtils.setupVTKObjectProgress(self, self._mc,
                                           'Extracting surface...')

        self._iObj = self._thresh
        self._oObj = self._mc
        
        self._viewFrame = self._createViewFrame({'threshold' :
                                                 self._thresh,
                                                 'reconstructionFilter' :
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
        del self._thresh
        del self._reconstructionFilter
        del self._mc
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
