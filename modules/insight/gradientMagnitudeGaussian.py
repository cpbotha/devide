# $Id$

import itk
import module_kits.itk_kit as itk_kit
from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin

class gradientMagnitudeGaussian(scriptedConfigModuleMixin, moduleBase):

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        self._config.gaussianSigma = 0.7
        self._config.normaliseAcrossScale = False

        configList = [
            ('Gaussian sigma', 'gaussianSigma', 'base:float', 'text',
             'Sigma in terms of image spacing.'),
            ('Normalise across scale', 'normaliseAcrossScale', 'base:bool',
             'checkbox', 'Determine normalisation factor.')]
        


        # setup the pipeline
        c = itk.GradientMagnitudeRecursiveGaussianImageFilter
        self._gradientMagnitude = c[itk.Image.F3, itk.Image.F3].New()
        
        itk_kit.utils.setupITKObjectProgress(
            self, self._gradientMagnitude,
            'itkGradientMagnitudeRecursiveGaussianImageFilter',
            'Calculating gradient image')
        
        scriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
             'itkGradientMagnitudeRecursiveGaussianImageFilter' :
             self._gradientMagnitude})
            
        self.sync_module_logic_with_config()
        
    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)
        # and the baseclass close
        moduleBase.close(self)
            
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
