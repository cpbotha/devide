from external import wxPyPlot
import genUtils
from moduleBase import moduleBase
from moduleMixins import introspectModuleMixin
import moduleUtils

try:
    import Numeric
except:
    import numarray as Numeric
    
import vtk
import wx

class histogram1D(introspectModuleMixin, moduleBase):

    """Calculates and shows 1D histogram (occurrences over value) of its
    input data.

    $Revision: 1.3 $
    """

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        self._imageAccumulate = vtk.vtkImageAccumulate()
        moduleUtils.setupVTKObjectProgress(self, self._imageAccumulate,
                                           'Calculating histogram')

        self._viewFrame = None
        self._createViewFrame()
        self._bindEvents()

        self._config.numberOfBins = 256
        self._config.minValue = 0.0
        self._config.maxValue = 256.0
        
        self.configToLogic()
        self.logicToConfig()
        self.configToView()

        self.view()

    def close(self):
        for i in range(len(self.getInputDescriptions())):
            self.setInput(i, None)

        self._viewFrame.Destroy()
        del self._viewFrame

        del self._imageAccumulate

        moduleBase.close(self)

    def getInputDescriptions(self):
        return ('VTK Image Data',)

    def setInput(self, idx, inputStream):

        self._imageAccumulate.SetInput(inputStream)

    def getOutputDescriptions(self):
        return ()

    def logicToConfig(self):
        # for now, we work on the first component (of a maximum of three)
        # we could make this configurable
        
        minValue = self._imageAccumulate.GetComponentOrigin()[0]
        
        cs = self._imageAccumulate.GetComponentSpacing()
        ce = self._imageAccumulate.GetComponentExtent()
        
        numberOfBins = ce[1] - ce[0] + 1
        # again we use nob - 1 so that maxValue is also part of a bin
        maxValue = minValue + (numberOfBins-1) * cs[0]

        self._config.numberOfBins = numberOfBins
        self._config.minValue = minValue
        self._config.maxValue = maxValue

    def configToLogic(self):
        co = list(self._imageAccumulate.GetComponentOrigin())
        co[0] = self._config.minValue
        self._imageAccumulate.SetComponentOrigin(co)

        ce = list(self._imageAccumulate.GetComponentExtent())

        ce[0] = 0
        ce[1] = self._config.numberOfBins - 1
        self._imageAccumulate.SetComponentExtent(ce)

        cs = list(self._imageAccumulate.GetComponentSpacing())
        # we divide by nob - 1 because we want maxValue to fall in the
        # last bin...
        cs[0] = (self._config.maxValue - self._config.minValue) / \
                (self._config.numberOfBins - 1)
        
        self._imageAccumulate.SetComponentSpacing(cs)
        
    def viewToConfig(self):
        self._config.numberOfBins = genUtils.textToInt(
            self._viewFrame.numBinsSpinCtrl.GetValue(),
            self._config.numberOfBins)

        self._config.minValue = genUtils.textToFloat(
            self._viewFrame.minValueText.GetValue(),
            self._config.minValue)

        self._config.maxValue = genUtils.textToFloat(
            self._viewFrame.maxValueText.GetValue(),
            self._config.maxValue)

        if self._config.minValue > self._config.maxValue:
            self._config.maxValue = self._config.minValue

    def configToView(self):
        self._viewFrame.numBinsSpinCtrl.SetValue(
            self._config.numberOfBins)

        self._viewFrame.minValueText.SetValue(
            str(self._config.minValue))

        self._viewFrame.maxValueText.SetValue(
            str(self._config.maxValue))

    def executeModule(self):
        if self._imageAccumulate.GetInput() == None:
            return
        
        self._imageAccumulate.Update()

        # get histogram params directly from logic
        minValue = self._imageAccumulate.GetComponentOrigin()[0]
        
        cs = self._imageAccumulate.GetComponentSpacing()
        ce = self._imageAccumulate.GetComponentExtent()
        
        numberOfBins = ce[1] - ce[0] + 1
        maxValue = minValue + numberOfBins * cs[0]
        # end of param extraction

        histArray = Numeric.arange(numberOfBins * 2)
        histArray.shape = (numberOfBins, 2)
        
        od = self._imageAccumulate.GetOutput()
        for i in range(numberOfBins):
            histArray[i,0] = minValue + i * cs[0]
            histArray[i,1] = od.GetScalarComponentAsDouble(i,0,0,0)

        lines = wxPyPlot.PolyLine(histArray, colour='blue')

        self._viewFrame.plotCanvas.Draw(
            wxPyPlot.PlotGraphics([lines], "Histogram", "Value", "Occurrences")
            )

    def view(self):
        self._viewFrame.Show()
        self._viewFrame.Raise()

    # ---------------------------------------------------------------
    # END of API methods
    # ---------------------------------------------------------------

    def _createViewFrame(self):
        # create the viewerFrame
        import modules.Viewers.resources.python.histogram1DFrames
        reload(modules.Viewers.resources.python.histogram1DFrames)

        self._viewFrame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager,
            modules.Viewers.resources.python.histogram1DFrames.\
            histogram1DFrame)

        self._viewFrame.plotCanvas.SetEnableZoom(True)
        self._viewFrame.plotCanvas.SetEnableGrid(True)

        objectDict = {'Module (self)' : self,
                      'vtkImageAccumulate' : self._imageAccumulate}

        moduleUtils.createStandardObjectAndPipelineIntrospection(
            self, self._viewFrame, self._viewFrame.viewFramePanel,
            objectDict, None)

        moduleUtils.createECASButtons(self, self._viewFrame,
                                      self._viewFrame.viewFramePanel)
        
        
                      
    def _bindEvents(self):
        wx.EVT_BUTTON(self._viewFrame,
                      self._viewFrame.autoRangeButton.GetId(),
                      self._handlerAutoRangeButton)

    def _handlerAutoRangeButton(self, event):
        if self._imageAccumulate.GetInput() == None:
            return

        self._imageAccumulate.GetInput().Update()
        sr = self._imageAccumulate.GetInput().GetScalarRange()
        self._viewFrame.minValueText.SetValue(str(sr[0]))
        self._viewFrame.maxValueText.SetValue(str(sr[1]))
