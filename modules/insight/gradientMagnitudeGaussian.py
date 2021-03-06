# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

import itk
import module_kits.itk_kit as itk_kit
from module_base import ModuleBase
from module_mixins import ScriptedConfigModuleMixin

class gradientMagnitudeGaussian(ScriptedConfigModuleMixin, ModuleBase):

    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        self._config.gaussianSigma = 0.7
        self._config.normaliseAcrossScale = False

        configList = [
            ('Gaussian sigma', 'gaussianSigma', 'base:float', 'text',
             'Sigma in terms of image spacing.'),
            ('Normalise across scale', 'normaliseAcrossScale', 'base:bool',
             'checkbox', 'Determine normalisation factor.')]
        


        # setup the pipeline
        self._gradientMagnitude = None
        img_type = itk.Image.F3
        self._create_pipeline(img_type)
        
        ScriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
             'itkGradientMagnitudeRecursiveGaussianImageFilter' :
             self._gradientMagnitude})
            
        self.sync_module_logic_with_config()
        
    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for input_idx in range(len(self.get_input_descriptions())):
            self.set_input(input_idx, None)

        # this will take care of all display thingies
        ScriptedConfigModuleMixin.close(self)
        # and the baseclass close
        ModuleBase.close(self)
            
        # remove all bindings
        del self._gradientMagnitude

    def execute_module(self):
        self._gradientMagnitude.Update()

    def get_input_descriptions(self):
        return ('ITK Image (3D, float)',)

    def set_input(self, idx, inputStream):
        try:
            self._gradientMagnitude.SetInput(inputStream)
        except TypeError, e:
            # deduce the type
            itku = itk_kit.utils
            ss = itku.get_img_type_and_dim_shortstring(inputStream)
            img_type = getattr(itk.Image,ss)
            # try to build a new pipeline (will throw exception if it
            # can't)
            self._create_pipeline(img_type)

            # re-apply config
            self.sync_module_logic_with_config()
            # connect input and hope it works.
            self._gradientMagnitude.SetInput(inputStream)


    def get_output_descriptions(self):
        return ('ITK Image',)

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

                                            
    def _create_pipeline(self, img_type):
        """Standard pattern to create ITK pipeline according to passed
        image type.
        """

        c = itk.GradientMagnitudeRecursiveGaussianImageFilter
        try:
            g = c[img_type, img_type].New()

        except KeyError, e:
            emsg = 'Could not create GradMag with input type %s. '\
                    'Please try a different input type.' % (ss,)
            raise TypeError, emsg

        # if successful, we can disconnect the old filter and store 
        # the instance (needed for the progress call!)
        if self._gradientMagnitude:
            self._gradientMagnitude.SetInput(None)

        self._gradientMagnitude = g

        itk_kit.utils.setupITKObjectProgress(
            self, self._gradientMagnitude,
            'itkGradientMagnitudeRecursiveGaussianImageFilter',
            'Calculating gradient image')

        
