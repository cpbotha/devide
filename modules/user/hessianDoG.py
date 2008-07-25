# $Id$

import fixitk as itk
import genUtils
from module_base import ModuleBase
import module_utils
import module_utilsITK
from moduleMixins import scriptedConfigModuleMixin

class hessianDoG(scriptedConfigModuleMixin, ModuleBase):
    """Calculates Hessian matrix of volume by convolution with second and
    cross derivatives of Gaussian kernel.


    $Revision: 1.1 $
    """
    
    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

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
        
        module_utilsITK.setupITKObjectProgress(
            self, g,
            'itkGradientMagnitudeRecursiveGaussianImageFilter',
            'Calculating gradient image')

        self._createWindow(
            {'Module (self)' : self,
             'itkGradientMagnitudeRecursiveGaussianImageFilter' :
             self._gradientMagnitude})

        self.config_to_logic()
        self.syncViewWithLogic()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)
        # and the baseclass close
        ModuleBase.close(self)
            
        # remove all bindings
        del self._gradientMagnitude

    def execute_module(self):
        self._gradientMagnitude.Update()

    def get_input_descriptions(self):
        return ('ITK Image (3D, float)',)

    def set_input(self, idx, inputStream):
        self._gradientMagnitude.SetInput(inputStream)

    def get_output_descriptions(self):
        return ('ITK Image (3D, float)',)

    def get_output(self, idx):
        return self._gradientMagnitude.GetOutput()

    def config_to_logic(self):
        self._gradientMagnitude.SetSigma(self._config.gaussianSigma)
        self._gradientMagnitude.SetNormalizeAcrossScale(
            self._config.normaliseAcrossScale)

    def logic_to_config(self):
        # durnit, there's no GetSigma().  Doh.
        self._config.normaliseAcrossScale = self._gradientMagnitude.\
                                            GetNormalizeAcrossScale()
