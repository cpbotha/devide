from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import moduleUtils
from wxPython.wx import *
import vtk

class voxelLinesToSurface(moduleBase, noConfigModuleMixin):
    """Given a binary volume, fit a surface through the marked points.

    A doubleThreshold could be used to extract points of interest from
    a volume.  By passing it through this module, a surface will be fit
    through those points of interest.

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
        self._thresh.ThresholdByUpper(1)
        self._del2d = vtk.vtkDelaunay2D()
        self._del2d.SetInput(self._thresh.GetOutput())
        self._geom = vtk.vtkGeometryFilter()
        self._geom.SetInput(self._del2d.GetOutput())

        #self._cast = vtk.vtkImageCast()
        #self._cast.SetOutputScalarType(vtk.VTK_SHORT)
        #self._distance = vtk.vtkImageCityBlockDistance()
        #self._distance.SetInput(self._cast.GetOutput())        
        #self._distance = vtk.vtkImageEuclideanDistance()
        #self._distance.ConsiderAnisotropyOn()

        moduleUtils.setupVTKObjectProgress(self, self._thresh,
                                           'Extracting geometry...')
        moduleUtils.setupVTKObjectProgress(self, self._del2d,
                                           'Calculating Delaunay3D...')
        moduleUtils.setupVTKObjectProgress(self, self._geom,
                                           'Extracting geometry...')
        
        
        

        self._iObj = self._thresh
        self._oObj = self._thresh
        
        self._viewFrame = self._createViewFrame({'thresh' :
                                                 self._thresh,
                                                 'delaunay3d' :
                                                 self._del2d})


    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)
        # don't forget to call the close() method of the vtkPipeline mixin
        noConfigModuleMixin.close(self)
        # get rid of our reference
        del self._thresh
        del self._del2d
        del self._geom
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
