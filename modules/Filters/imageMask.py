import genUtils
from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import moduleUtils
import wx
import vtk

class imageMask(moduleBase, noConfigModuleMixin):

    """The input data (input 1) is masked with the mask (input 2).

    The output image is identical to the input image wherever the mask has
    a value.  The output image is 0 everywhere else.
    """
    
    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)
        noConfigModuleMixin.__init__(self)

        self._imageMask = vtk.vtkImageMask()
        self._imageMask.SetMaskedOutputValue(0)
        self._imageMask.GetOutput().SetUpdateExtentToWholeExtent()
        
        moduleUtils.setupVTKObjectProgress(self, self._imageMask,
                                           'Masking image')

        self._viewFrame = self._createViewFrame(
            {'vtkImageMask' : self._imageMask})

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
        del self._imageMask

    def getInputDescriptions(self):
        return ('vtkImageData (data)', 'vtkImageData (mask)')

    def setInput(self, idx, inputStream):
        if idx == 0:
            self._imageMask.SetImageInput(inputStream)
        else:
            self._imageMask.SetMaskInput(inputStream)

    def getOutputDescriptions(self):
        return (self._imageMask.GetOutput().GetClassName(), )

    def getOutput(self, idx):
        return self._imageMask.GetOutput()

    def logicToConfig(self):
        pass
    
    def configToLogic(self):
        pass
    
    def viewToConfig(self):
        pass

    def configToView(self):
        pass
    
    def executeModule(self):
        self._imageMask.Update()

    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        self._viewFrame.Show(True)
        self._viewFrame.Raise()


