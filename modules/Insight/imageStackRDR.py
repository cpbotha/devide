from genMixins import subjectMixin, updateCallsExecuteModuleMixin
import InsightToolkit as itk
from moduleBase import moduleBase
import wx

class imageStackClass(list,
                      subjectMixin,
                      updateCallsExecuteModuleMixin):
    
    def __init__(self, d3Module):
        # call base ctors
        subjectMixin.__init__(self)
        updateCallsExecuteModuleMixin.__init__(self, d3Module)

    def close(self):
        subjectMixin.close(self)
        updateCallsExecuteModuleMixin.close(self)
        
    

class imageStackRDR(moduleBase):
    """Loads a list of images as ITK Images.

    This list can e.g. be used as input to the 2D registration module.
    """

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        # list of ACTUAL itk images
        self._imageStack = imageStackClass(self)

        self._viewFrame = None
        self._createViewFrame()

        # list of names that are to be loaded
        self._config._imageFileNames
        # we'll use this variable to check when we need to reload
        # filenames.
        self._imageFileNamesChanged = True

        self.configToLogic()
        self.syncViewWithLogic()

    def close(self):
        # take care of our refs to all the loaded images
        self._imageStack.close()
        self._imageStack = []
        # destroy GUI
        self._viewFrame.Destroy()
        # base classes taken care of
        moduleBase.close(self)

    def getInputDescriptions(self):
        return ()

    def setInput(self, idx, inputStream):
        raise Exception

    def getOutputDescriptions(self):
        return ('ITK Image Stack',)

    def getOutput(self, idx):
        return self._imageStack

    def logicToConfig(self):
        pass

    def configToLogic(self):
        pass

    def viewToConfig(self):
        count = self._viewFrame.fileNamesListBox.GetCount()
        tempList = []
        for n in range(count):
            tempList.append(self._viewFrame.fileNamesListBox.GetString(n))

        
        if tempList != self._config._imageFileNames:
            # this is a new list
            self._imageFileNamesChanged = True
            # copy it...


    def configToView(self):
        stdText = '(%.2f, %.2f, %.2f)' % self._config.standardDeviation
        self._viewFrame.stdTextCtrl.SetValue(stdText)

        cutoffText = '(%.2f, %.2f, %.2f)' % self._config.radiusCutoff
        self._viewFrame.radiusCutoffTextCtrl.SetValue(cutoffText)

    def executeModule(self):
        self._imageGaussianSmooth.Update()

    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()

    def _createViewFrame(self):
        self._moduleManager.importReload(
            'modules.Filters.resources.python.imageGaussianSmoothViewFrame')
        import modules.Filters.resources.python.imageGaussianSmoothViewFrame

        self._viewFrame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager,
            modules.Filters.resources.python.imageGaussianSmoothViewFrame.\
            imageGaussianSmoothViewFrame)

        objectDict = {'vtkImageGaussianSmooth' : self._imageGaussianSmooth}
        moduleUtils.createStandardObjectAndPipelineIntrospection(
            self, self._viewFrame, self._viewFrame.viewFramePanel,
            objectDict, None)

        moduleUtils.createECASButtons(self, self._viewFrame,
                                      self._viewFrame.viewFramePanel)

        

