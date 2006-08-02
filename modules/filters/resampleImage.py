# imageGaussianSmooth copyright (c) 2003 by Charl P. Botha cpbotha@ieee.org
# $Id$
# performs image smoothing by convolving with a Gaussian

import genUtils
from moduleBase import moduleBase
from moduleMixins import vtkPipelineConfigModuleMixin
import moduleUtils
import vtk

class resampleImage(moduleBase, vtkPipelineConfigModuleMixin):

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        self._imageResample = vtk.vtkImageResample()

        moduleUtils.setupVTKObjectProgress(self, self._imageResample,
                                           'Resampling image.')
        


        # 0: nearest neighbour
        # 1: linear
        # 2: cubic
        self._config.interpolationMode = 1
        self._config.magFactors = [1.0, 1.0, 1.0]

        self._viewFrame = None
        self._createViewFrame()

        self.configToLogic()
        self.logicToConfig()
        self.configToView()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        self.setInput(0, None)
        # don't forget to call the close() method of the vtkPipeline mixin
        vtkPipelineConfigModuleMixin.close(self)
        # take out our view interface
        self._viewFrame.Destroy()
        # get rid of our reference
        del self._imageResample
        # and finally call our base dtor
        moduleBase.close(self)
        
    def getInputDescriptions(self):
        return ('vtkImageData',)

    def setInput(self, idx, inputStream):
        self._imageResample.SetInput(inputStream)

    def getOutputDescriptions(self):
        return (self._imageResample.GetOutput().GetClassName(),)

    def getOutput(self, idx):
        return self._imageResample.GetOutput()

    def logicToConfig(self):
        istr = self._imageResample.GetInterpolationModeAsString()
        # we do it this way so that when the values in vtkImageReslice
        # are changed, we won't be affected
        self._config.interpolationMode = {'NearestNeighbor': 0,
                                          'Linear': 1,
                                          'Cubic': 2}[istr]

        
        for i in range(3):
            mfi = self._imageResample.GetAxisMagnificationFactor(i, None)
            self._config.magFactors[i] = mfi

    def configToLogic(self):
        if self._config.interpolationMode == 0:
            self._imageResample.SetInterpolationModeToNearestNeighbor()
        elif self._config.interpolationMode == 1:
            self._imageResample.SetInterpolationModeToLinear()
        else:
            self._imageResample.SetInterpolationModeToCubic()

        for i in range(3):
            self._imageResample.SetAxisMagnificationFactor(
                i, self._config.magFactors[i])

    def viewToConfig(self):
        itc = self._viewFrame.interpolationTypeChoice.GetSelection()
        if itc < 0 or itc > 2:
            # default when something weird happens to choice
            itc = 1

        self._config.interpolationMode = itc

        txtTup = self._viewFrame.magFactorXText.GetValue(), \
                 self._viewFrame.magFactorYText.GetValue(), \
                 self._viewFrame.magFactorZText.GetValue()

        for i in range(3):
            self._config.magFactors[i] = genUtils.textToFloat(
                txtTup[i], self._config.magFactors[i])
            
        
    def configToView(self):
        self._viewFrame.interpolationTypeChoice.SetSelection(
            self._config.interpolationMode)

        txtTup = self._viewFrame.magFactorXText, \
                 self._viewFrame.magFactorYText, \
                 self._viewFrame.magFactorZText
        
        for i in range(3):
            txtTup[i].SetValue(str(self._config.magFactors[i]))
        
    
    def executeModule(self):
        self._imageResample.Update()
        

    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()

    def _createViewFrame(self):
        self._moduleManager.importReload(
            'modules.filters.resources.python.resampleImageViewFrame')
        import modules.filters.resources.python.resampleImageViewFrame

        self._viewFrame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager,
            modules.filters.resources.python.resampleImageViewFrame.\
            resampleImageViewFrame)

        objectDict = {'vtkImageResample' : self._imageResample}
        moduleUtils.createStandardObjectAndPipelineIntrospection(
            self, self._viewFrame, self._viewFrame.viewFramePanel,
            objectDict, None)

        moduleUtils.createECASButtons(self, self._viewFrame,
                                      self._viewFrame.viewFramePanel)
