import genUtils
from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import moduleUtils
import wx
import vtk

class imageFlip(moduleBase, noConfigModuleMixin):

    """Flips image (volume) with regards to a single axis.

    At the moment, this flips by default about Z.  You can change this by
    introspecting and calling the SetFilteredAxis() method via the
    object inspection.
    """
    
    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)
        noConfigModuleMixin.__init__(self)

        self._imageFlip = vtk.vtkImageFlip()
        self._imageFlip.SetFilteredAxis(2)
        self._imageFlip.GetOutput().SetUpdateExtentToWholeExtent()
        
        moduleUtils.setupVTKObjectProgress(self, self._imageFlip,
                                           'Flipping image')

        self._viewFrame = self._createViewFrame(
            {'vtkImageFlip' : self._imageFlip})

        # pass the data down to the underlying logic
        self.configToLogic()
        # and all the way up from logic -> config -> view to make sure
        self.syncViewWithLogic()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)

        # this will take care of all display thingies
        noConfigModuleMixin.close(self)
        
        # get rid of our reference
        del self._imageFlip

    def getInputDescriptions(self):
        return ('vtkImageData',)

    def setInput(self, idx, inputStream):
        self._imageFlip.SetInput(inputStream)

    def getOutputDescriptions(self):
        return (self._imageFlip.GetOutput().GetClassName(), )

    def getOutput(self, idx):
        return self._imageFlip.GetOutput()

    def logicToConfig(self):
        pass
    
    def configToLogic(self):
        pass
    
    def viewToConfig(self):
        pass

    def configToView(self):
        pass
    
    def executeModule(self):
        self._imageFlip.Update()

    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        self._viewFrame.Show(True)
        self._viewFrame.Raise()


