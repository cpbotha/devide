import genUtils
from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import moduleUtils
import wx
import vtk
from module_kits.vtk_kit.mixins import VTKErrorFuncMixin

class imageGradientMagnitude(moduleBase, noConfigModuleMixin,
                             VTKErrorFuncMixin):

    """Calculates the gradient magnitude of the input volume using central
    differences.

    $Revision: 1.5 $
    """
    
    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)
        noConfigModuleMixin.__init__(self)

        self._imageGradientMagnitude = vtk.vtkImageGradientMagnitude()
        self._imageGradientMagnitude.SetDimensionality(3)
        
        moduleUtils.setupVTKObjectProgress(self, self._imageGradientMagnitude,
                                           'Calculating gradient magnitude')
        self.add_vtk_error_handler(self._imageGradientMagnitude)

        self._viewFrame = self._createViewFrame(
            {'Module (self)' : self,
             'vtkImageGradientMagnitude' : self._imageGradientMagnitude})

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
        noConfigModuleMixin.close(self)

        moduleBase.close(self)
        
        # get rid of our reference
        del self._imageGradientMagnitude

    def getInputDescriptions(self):
        return ('vtkImageData',)

    def setInput(self, idx, inputStream):
        self._imageGradientMagnitude.SetInput(inputStream)

    def getOutputDescriptions(self):
        return (self._imageGradientMagnitude.GetOutput().GetClassName(), )

    def getOutput(self, idx):
        return self._imageGradientMagnitude.GetOutput()

    def logicToConfig(self):
        pass
    
    def configToLogic(self):
        pass
    
    def viewToConfig(self):
        pass

    def configToView(self):
        pass
    
    def executeModule(self):
        self._imageGradientMagnitude.Update()
        self.check_vtk_error()

    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        self._viewFrame.Show(True)
        self._viewFrame.Raise()


