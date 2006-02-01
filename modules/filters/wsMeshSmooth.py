import genUtils
from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtk
from module_kits.vtk_kit.mixins import VTKErrorFuncMixin

class wsMeshSmooth(scriptedConfigModuleMixin, moduleBase, VTKErrorFuncMixin):
    """Module that runs vtkWindowedSincPolyDataFilter on its input data for
    mesh smoothing.
    """
    
    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)
        

        self._wsPDFilter = vtk.vtkWindowedSincPolyDataFilter()

        moduleUtils.setupVTKObjectProgress(self, self._wsPDFilter,
                                           'Smoothing polydata')
        self.add_vtk_error_handler(self._wsPDFilter)

        # setup some defaults
        self._config.numberOfIterations = 20
        self._config.passBand = 0.1
        self._config.featureEdgeSmoothing = False
        self._config.boundarySmoothing = True

        config_list = [
            ('Number of iterations', 'numberOfIterations', 'base:int', 'text',
             'Algorithm will stop after this many iterations.'),
            ('Pass band (0 - 2, default 0.1)', 'passBand', 'base:float',
             'text', 'Indication of frequency cut-off, the lower, the more '
             'it smoothes.'),
            ('Feature edge smoothing', 'featureEdgeSmoothing', 'base:bool',
             'checkbox', 'Smooth feature edges (large dihedral angle)'),
            ('Boundary smoothing', 'boundarySmoothing', 'base:bool',
             'checkbox', 'Smooth boundary edges (edges with only one face).')]

        scriptedConfigModuleMixin.__init__(self, config_list)

        self._viewFrame = self._createWindow(
            {'Module (self)' : self,
             'vtkWindowedSincPolyDataFilter' : self._wsPDFilter})
   
        # pass the data down to the underlying logic
        self.configToLogic()
        # and all the way up from logic -> config -> view to make sure
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
        del self._wsPDFilter

    def getInputDescriptions(self):
        return ('vtkPolyData',)

    def setInput(self, idx, inputStream):
        self._wsPDFilter.SetInput(inputStream)

    def getOutputDescriptions(self):
        return (self._wsPDFilter.GetOutput().GetClassName(), )

    def getOutput(self, idx):
        return self._wsPDFilter.GetOutput()

    def logicToConfig(self):
        self._config.numberOfIterations = self._wsPDFilter.\
                                          GetNumberOfIterations()
        self._config.passBand = self._wsPDFilter.GetPassBand()
        self._config.featureEdgeSmoothing = bool(
            self._wsPDFilter.GetFeatureEdgeSmoothing())
        self._config.boundarySmoothing = bool(
            self._wsPDFilter.GetBoundarySmoothing())

    def configToLogic(self):
        self._wsPDFilter.SetNumberOfIterations(self._config.numberOfIterations)
        self._wsPDFilter.SetPassBand(self._config.passBand)
        self._wsPDFilter.SetFeatureEdgeSmoothing(
            self._config.featureEdgeSmoothing)
        self._wsPDFilter.SetBoundarySmoothing(
            self._config.boundarySmoothing)


    def executeModule(self):
        self._wsPDFilter.Update()
        self.check_vtk_error()

