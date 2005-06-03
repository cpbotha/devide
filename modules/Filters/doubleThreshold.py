import genUtils
from moduleBase import moduleBase
from moduleMixins import vtkPipelineConfigModuleMixin
import moduleUtils
import vtk

class doubleThreshold(moduleBase,
                         vtkPipelineConfigModuleMixin):

    def __init__(self, moduleManager):

        # call parent constructor
        moduleBase.__init__(self, moduleManager)

        self._imageThreshold = vtk.vtkImageThreshold()

        moduleUtils.setupVTKObjectProgress(self, self._imageThreshold,
                                           'Thresholding data')

        self._outputTypes = {'Double': 'VTK_DOUBLE',
                             'Float' : 'VTK_FLOAT',
                             'Long'  : 'VTK_LONG',
                             'Unsigned Long' : 'VTK_UNSIGNED_LONG',
                             'Integer' : 'VTK_INT',
                             'Unsigned Integer' : 'VTK_UNSIGNED_INT',
                             'Short' : 'VTK_SHORT',
                             'Unsigned Short' : 'VTK_UNSIGNED_SHORT',
                             'Char' : 'VTK_CHAR',
                             'Unsigned Char' : 'VTK_UNSIGNED_CHAR',
                             'Same as input' : -1}

        self._viewFrame = None
        self._createViewFrame()

        # now setup some defaults before our sync
        self._config.lowerThreshold = 1250
        self._config.upperThreshold = 2500
        #self._config.rtu = 1
        self._config.replaceIn = 1
        self._config.inValue = 1
        self._config.replaceOut = 1
        self._config.outValue = 0
        self._config.outputScalarType = self._imageThreshold.GetOutputScalarType()

        # transfer these defaults to the logic
        self.configToLogic()

        # then make sure they come all the way back up via self._config
        self.syncViewWithLogic()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        self.setInput(0, None)
        # close down the vtkPipeline stuff
        vtkPipelineConfigModuleMixin.close(self)
        # take out our view interface
        self._viewFrame.Destroy()
        # get rid of our reference
        del self._imageThreshold

    def getInputDescriptions(self):
	return ('vtkImageData',)
    

    def setInput(self, idx, inputStream):
        self._imageThreshold.SetInput(inputStream)
        if not inputStream is None:
            # get scalar bounds
            minv, maxv = inputStream.GetScalarRange()

    def getOutputDescriptions(self):
	return ('Thresholded data (vtkImageData)',)
    

    def getOutput(self, idx):
        return self._imageThreshold.GetOutput()

    def logicToConfig(self):
        self._config.lowerThreshold = self._imageThreshold.GetLowerThreshold()
        self._config.upperThreshold = self._imageThreshold.GetUpperThreshold()
        self._config.replaceIn = self._imageThreshold.GetReplaceIn()
        self._config.inValue = self._imageThreshold.GetInValue()
        self._config.replaceOut = self._imageThreshold.GetReplaceOut()
        self._config.outValue = self._imageThreshold.GetOutValue()
        self._config.outputScalarType = self._imageThreshold.GetOutputScalarType()

    def configToLogic(self):
        self._imageThreshold.ThresholdBetween(self._config.lowerThreshold, self._config.upperThreshold)
        # SetInValue HAS to be called before SetReplaceIn(), as SetInValue()
        # always toggles SetReplaceIn() to ON
        self._imageThreshold.SetInValue(self._config.inValue)        
        self._imageThreshold.SetReplaceIn(self._config.replaceIn)
        # SetOutValue HAS to be called before SetReplaceOut(), same reason
        # as above
        self._imageThreshold.SetOutValue(self._config.outValue)
        self._imageThreshold.SetReplaceOut(self._config.replaceOut)
        self._imageThreshold.SetOutputScalarType(self._config.outputScalarType)

    def viewToConfig(self):
        self._config.lowerThreshold = self._sanitiseThresholdTexts(0)
        self._config.upperThreshold = self._sanitiseThresholdTexts(1)
        self._config.replaceIn = self._viewFrame.replaceInCheckBox.GetValue()
        self._config.inValue = float(self._viewFrame.replaceInText.GetValue())
        self._config.replaceOut = self._viewFrame.replaceOutCheckBox.GetValue()
        self._config.outValue = float(self._viewFrame.replaceOutText.GetValue())

        ocString = self._viewFrame.outputDataTypeChoice.GetStringSelection()
        if len(ocString) == 0:
            genUtils.logError("Impossible error with outputType choice in "
                              "doubleThresholdFLT.py.  Picking sane default.")
            # set to last string in list, should be default
            ocString = self._outputTypes.keys()[-1]

        try:
            symbolicOutputType = self._outputTypes[ocString]
        except KeyError:
            genUtils.logError("Impossible error with ocString in "
                              "doubleThresholdFLT.py.  Picking sane default.")
            # set to last string in list, should be default
            symbolicOutputType = self._outputTypes.values()[-1]

        if symbolicOutputType == -1:
            self._config.outputScalarType = -1
        else:
            try:
                self._config.outputScalarType = getattr(vtk, symbolicOutputType)
            except AttributeError:
                genUtils.logError("Impossible error with symbolicOutputType "
                                  "in doubleThresholdFLT.py.  Picking sane "
                                  "default.")
                self._config.outputScalarType = -1

    def configToView(self):
        self._viewFrame.lowerThresholdText.SetValue("%.2f" % (self._config.lowerThreshold))
        self._viewFrame.upperThresholdText.SetValue("%.2f" % (self._config.upperThreshold))
        self._viewFrame.replaceInCheckBox.SetValue(self._config.replaceIn)
        self._viewFrame.replaceInText.SetValue(str(self._config.inValue))
        self._viewFrame.replaceOutCheckBox.SetValue(self._config.replaceOut)
        self._viewFrame.replaceOutText.SetValue(str(self._config.outValue))

        for key in self._outputTypes.keys():
            symbolicOutputType = self._outputTypes[key]
            if hasattr(vtk, str(symbolicOutputType)):
                numericOutputType = getattr(vtk, symbolicOutputType)
            else:
                numericOutputType = -1
                
            if self._config.outputScalarType == numericOutputType:
                break

        self._viewFrame.outputDataTypeChoice.SetStringSelection(key)

    def executeModule(self):
        # don't ask... we have to call Update() twice here, I _think_
        # due to weirdness in vtkImageThreshold() that I haven't been
        # able to track down.  If update is called only once, a
        # directly connected slice3dVWR will Render() but only show
        # the PREVIOUS output of the _imageThreshold.  My current
        # hypothesis is that this is due to the ThreadedExecute
        # employed by vtkImageThreshold, i.e. Update() is
        # non-blocking.  This hypothesis is of course still full of
        # holes. :)
        self._imageThreshold.Update()
        #self._imageThreshold.Update()

        # fixed it now by adding observer to EndEvent of source of data
        # input in sliceviewer

    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()

    def _createViewFrame(self):

        # import the viewFrame (created with wxGlade)
        import modules.Filters.resources.python.doubleThresholdFLTFrame
        reload(modules.Filters.resources.python.doubleThresholdFLTFrame)

        self._viewFrame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager,
            modules.Filters.resources.python.doubleThresholdFLTFrame.\
            doubleThresholdFLTFrame)

        objectDict = {'imageThreshold' : self._imageThreshold}
        moduleUtils.createStandardObjectAndPipelineIntrospection(
            self, self._viewFrame, self._viewFrame.viewFramePanel,
            objectDict, None)

        moduleUtils.createECASButtons(self, self._viewFrame,
                                      self._viewFrame.viewFramePanel)

        # finish setting up the output datatype choice
        self._viewFrame.outputDataTypeChoice.Clear()
        for aType in self._outputTypes.keys():
            self._viewFrame.outputDataTypeChoice.Append(aType)    

    def _sanitiseThresholdTexts(self, whichText):
        if whichText == 0:
            try:
                lower = float(self._viewFrame.lowerThresholdText.GetValue())
            except ValueError:
                # this means that the user did something stupid, so we
                # restore the value to what's in our config
                self._viewFrame.lowerThresholdText.SetValue(str(
                    self._config.lowerThreshold))
                
                return self._config.lowerThreshold
                
            # lower is the new value...
            upper = float(self._viewFrame.upperThresholdText.GetValue())
            if lower > upper:
                lower = upper
                self._viewFrame.lowerThresholdText.SetValue(str(lower))

            return lower

        else:
            try:
                upper = float(self._viewFrame.upperThresholdText.GetValue())
            except ValueError:
                # this means that the user did something stupid, so we
                # restore the value to what's in our config
                self._viewFrame.upperThresholdText.SetValue(str(
                    self._config.upperThreshold))
                
                return self._config.upperThreshold

            # upper is the new value
            lower = float(self._viewFrame.lowerThresholdText.GetValue())
            if upper < lower:
                upper = lower
                self._viewFrame.upperThresholdText.SetValue(str(upper))

            return upper
