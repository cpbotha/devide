from genMixins import subjectMixin, updateCallsExecuteModuleMixin
import InsightToolkit as itk
from moduleBase import moduleBase
from moduleMixins import fileOpenDialogModuleMixin
import moduleUtils
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

class imageStackRDR(moduleBase, fileOpenDialogModuleMixin):
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
        self._config._imageFileNames = []
        # we'll use this variable to check when we need to reload
        # filenames.
        self._imageFileNamesChanged = True
        #

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
            # copy...
            self._config._imageFileNames = tempList
            
    def configToView(self):
        # clear wxListBox
        self._viewFrame.fileNamesListBox.Clear()
        for fileName in self._config._imageFileNames:
            self._viewFrame.fileNamesListBox.Append(fileName)

    def executeModule(self):
        if self._imageFileNamesChanged:
            # only if things have changed do we do our thing
            # first take care of old refs
            del self._imageStack[:]

            # setup for progress counter
            currentProgress = 0.0
            if len(self._config._imageFileNames) > 0:
                progressStep = 100.0 / len(self._config._imageFileNames)
            else:
                progressStep = 100.0
                
            for imageFileName in self._config._imageFileNames:
                self._moduleManager.setProgress(
                    currentProgress, "Loading %s" % (imageFileName,))
                currentProgress += progressStep
                
                reader = itk.itkImageFileReaderF2_New()
                reader.SetFileName(imageFileName)
                reader.Update()
                self._imageStack.append(reader.GetOutput())

            self._moduleManager.setProgress(100.0, "Done loading images.")
            # make sure all observers know about the changes
            self._imageStack.notify()
            # indicate that we're in sync now
            self._imageFileNamesChanged = False

    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()

    def _bindEvents(self):
        wx.EVT_BUTTON(self._viewFrame, self._viewFrame.addButtonId,
                      self._handlerAddButton)

    def _createViewFrame(self):
        self._moduleManager.importReload(
            'modules.Insight.resources.python.imageStackRDRViewFrame')
        import modules.Insight.resources.python.imageStackRDRViewFrame

        self._viewFrame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager,
            modules.Insight.resources.python.imageStackRDRViewFrame.\
            imageStackRDRViewFrame)

        moduleUtils.createECASButtons(self, self._viewFrame,
                                      self._viewFrame.viewFramePanel)

        self._bindEvents()

    def _handlerAddButton(self, event):
        fres = self.filenameBrowse(self._viewFrame,
                                   "Select files to add to stack",
                                   "*", wx.OPEN | wx.MULTIPLE)
        if fres:
            for fileName in fres:
                self._viewFrame.fileNamesListBox.Append(fileName)
                
            
