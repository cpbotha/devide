# imageGaussianSmooth copyright (c) 2003 by Charl P. Botha cpbotha@ieee.org
# $Id: imageGaussianSmooth.py,v 1.2 2003/09/21 18:56:46 cpbotha Exp $
# performs image smoothing by convolving with a Gaussian

import genUtils
from moduleBase import moduleBase
from moduleMixins import vtkPipelineConfigModuleMixin
import moduleUtils
from wxPython.wx import *
import vtk

class imageGaussianSmooth(moduleBase, vtkPipelineConfigModuleMixin):

    def __init__(self, moduleManager):
        moduleBase.__init__(moduleManager)

        self._imageGaussianSmooth = vtk.vtkImageGaussianSmooth()

        moduleUtils.setupVTKObjectProgress(self, self._imageGaussianSmooth,
                                           'Smoothing image with Gaussian')

        self._config.standardDeviation = (2.0, 2.0, 2.0)
        self._config.radiusCutoff = (1.5, 1.5, 1.5)

        self._viewFrame = None
        self._createViewFrame()

        self.configToLogic()
        self.syncViewWithLogic()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        self.setInput(0, None)
        # don't forget to call the close() method of the vtkPipeline mixin
        vtkPipelineConfigModuleMixin.close(self)
        # take out our view interface
        self._viewFrame.Destroy()
        # get rid of our reference
        del self._imageGaussianSmooth
        # and finally call our base dtor
        moduleBase.close(self)
        
    def getInputDescriptions(self):
        return ('vtkImageData',)

    def setInput(self, idx, inputStream):
        self._imageGaussianSmooth.SetInput(inputStream)

    def getOutputDescriptions(self):
        return (self._imageGaussianSmooth.GetOutput().GetClassName(),)

    def getOutput(self, idx):
        return self._imageGaussianSmooth.GetOutput()

    def logicToConfig(self):
        self._config.standardDeviation = self._imageGaussianSmooth.\
                                         GetStandardDeviations()
        self._config.radiusCutoff = self._imageGaussianSmooth.\
                                    GetRadiusFactors()

    def configToLogic(self):
        self._imageGaussianSmooth.SetStandardDeviations(
            self._config.standardDeviation)
        self._imageGaussianSmooth.SetRadiusFactors(
            self._config.radiusCutoff)

    def viewToConfig(self):
        # continue with textToTuple in genUtils
        pass
