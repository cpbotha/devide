import genUtils
from moduleBase import moduleBase
from moduleMixins import vtkPipelineConfigModuleMixin
import moduleUtils
import vtk

class wsMeshSmooth(moduleBase, vtkPipelineConfigModuleMixin):
    """Module that runs vtkWindowedSincPolyDataFilter on its input data for
    mesh smoothing.
    """
    
    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)

        self._wsPDFilter = vtk.vtkWindowedSincPolyDataFilter()

        moduleUtils.setupVTKObjectProgress(self, self._wsPDFilter,
                                           'Smoothing polydata')

        # setup some defaults
        self._config.numberOfIterations = 20
        self._config.passBand = 0.1
        self._config.featureEdgeSmoothing = False
        self._config.boundarySmoothing = True

        # create and setup the viewFrame
        self._viewFrame = self._createViewFrame()

        # pass the data down to the underlying logic
        self.configToLogic()
        # and all the way up from logic -> config -> view to make sure
        self.syncViewWithLogic()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)
        
        # get rid of our reference
        del self._wsPDFilter

        # takes care of inspection windows explicitly
        vtkPipelineConfigModuleMixin.close(self)

        self._viewFrame.Destroy()
        del self._viewFrame

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

    def viewToConfig(self):
        self._config.numberOfIterations = genUtils.textToInt(
            self._viewFrame.smoothingIterationsText.GetValue(),
            self._config.numberOfIterations)

        self._config.passBand = genUtils.textToFloat(
            self._viewFrame.passBandText.GetValue(),
            self._config.passBand)

        self._config.featureEdgeSmoothing =  bool(
            self._viewFrame.featureEdgeSmoothingCheckBox.GetValue())

        self._config.boundarySmoothing = bool(
            self._viewFrame.boundarySmoothingCheckBox.GetValue())
        

    def configToView(self):
        self._viewFrame.smoothingIterationsText.SetValue(
            "%d" % (self._config.numberOfIterations,))
        self._viewFrame.passBandText.SetValue(
            "%.2f" % (self._config.passBand,))
        self._viewFrame.featureEdgeSmoothingCheckBox.SetValue(
            bool(self._config.featureEdgeSmoothing))
        self._viewFrame.boundarySmoothingCheckBox.SetValue(
            bool(self._config.boundarySmoothing))

    def executeModule(self):
        self._wsPDFilter.Update()

    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()

    def _createViewFrame(self):

        mm = self._moduleManager
        # import/reload the viewFrame (created with wxGlade)
        mm.importReload(
            'modules.Filters.resources.python.wsMeshSmoothFLTViewFrame')
        # this line is harmless due to Python's import caching, but we NEED
        # to do it so that the Installer knows that this devide module
        # requires it and so that it's available in this namespace.
        import modules.Filters.resources.python.wsMeshSmoothFLTViewFrame

        # instantiate the view frame, add close handler, set default icon
        viewFrame = moduleUtils.instantiateModuleViewFrame(
            self, mm,
            modules.Filters.resources.python.wsMeshSmoothFLTViewFrame.\
            wsMeshSmoothFLTViewFrame)

        # setup introspection with default everythings
        objectDict = {'vtkWindowedSincPolyDataFilter': self._wsPDFilter}
        moduleUtils.createStandardObjectAndPipelineIntrospection(
            self, viewFrame, viewFrame.viewFramePanel,
            objectDict, None)

        # create and configure the standard ECAS buttons
        moduleUtils.createECASButtons(self, viewFrame,
                                      viewFrame.viewFramePanel)

        # return it so that it gets assigned to the correct ivar
        return viewFrame
