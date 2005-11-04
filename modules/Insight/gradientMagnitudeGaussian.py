# $Id: gradientMagnitudeGaussian.py,v 1.4 2005/11/04 10:34:55 cpbotha Exp $

import fixitk as itk
import genUtils
from moduleBase import moduleBase
import moduleUtils
import moduleUtilsITK
from moduleMixins import scriptedConfigModuleMixin

class gradientMagnitudeGaussian(scriptedConfigModuleMixin, moduleBase):
    """Calculates gradient magnitude of an image by convolving with the
    derivative of a Gaussian.

    $Revision: 1.4 $
    """
    
    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        self._config.gaussianSigma = 0.7
        self._config.normaliseAcrossScale = False

        configList = [
            ('Gaussian sigma', 'gaussianSigma', 'base:float', 'text',
             'Sigma in terms of image spacing.'),
            ('Normalise across scale', 'normaliseAcrossScale', 'base:bool',
             'checkbox', 'Determine normalisation factor.')]
        
        scriptedConfigModuleMixin.__init__(self, configList)

        # setup the pipeline
        g = itk.itkGradientMagnitudeRecursiveGaussianImageFilterF3F3_New()
        self._gradientMagnitude = g
        
        moduleUtilsITK.setupITKObjectProgress(
            self, g,
            'itkGradientMagnitudeRecursiveGaussianImageFilter',
            'Calculating gradient image')

        self._createWindow(
            {'Module (self)' : self,
             'itkGradientMagnitudeRecursiveGaussianImageFilter' :
             self._gradientMagnitude})

        self.configToLogic()
        self.logicToConfig()
        self.configToView()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)
        # and the baseclass close
        moduleBase.close(self)
            
        # remove all bindings
        del self._gradientMagnitude

    def executeModule(self):
        self._gradientMagnitude.Update()

    def getInputDescriptions(self):
        return ('ITK Image (3D, float)',)

    def setInput(self, idx, inputStream):
        self._gradientMagnitude.SetInput(inputStream)

    def getOutputDescriptions(self):
        return ('ITK Image (3D, float)',)

    def getOutput(self, idx):
        return self._gradientMagnitude.GetOutput()

    def configToLogic(self):
        self._gradientMagnitude.SetSigma(self._config.gaussianSigma)
        self._gradientMagnitude.SetNormalizeAcrossScale(
            self._config.normaliseAcrossScale)

    def logicToConfig(self):
        # durnit, there's no GetSigma().  Doh.
        self._config.normaliseAcrossScale = self._gradientMagnitude.\
                                            GetNormalizeAcrossScale()
