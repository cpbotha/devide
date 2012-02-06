# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

import itk
import module_kits.itk_kit as itk_kit
from module_base import ModuleBase
from module_mixins import ScriptedConfigModuleMixin

class geodesicActiveContour(ScriptedConfigModuleMixin, ModuleBase):


    def __init__(self, module_manager):

        ModuleBase.__init__(self, module_manager)
        
        # setup defaults
        self._config.propagationScaling = 1.0
        self._config.curvatureScaling = 1.0
        self._config.advectionScaling = 1.0
        self._config.numberOfIterations = 100
        
        configList = [
            ('Propagation scaling:', 'propagationScaling', 'base:float',
             'text', 'Propagation scaling parameter for the geodesic active '
             'contour, '
             'i.e. balloon force.  Positive for outwards, negative for '
             'inwards.'),
            ('Curvature scaling:', 'curvatureScaling', 'base:float',
             'text', 'Curvature scaling term weighting.'),
            ('Advection scaling:', 'advectionScaling', 'base:float',
             'text', 'Advection scaling term weighting.'),
            ('Number of iterations:', 'numberOfIterations', 'base:int',
             'text',
             'Number of iterations that the algorithm should be run for')]
        
        ScriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self})

        # create all pipeline thingies
        self._geodesicActiveContour = None
        self._create_pipeline(itk.Image.F3)

        self.sync_module_logic_with_config()
        
    def close(self):
        self._destroyITKPipeline()
        ScriptedConfigModuleMixin.close(self)
        ModuleBase.close(self)

    def execute_module(self):
        self.get_output(0).Update()
        self._module_manager.setProgress(
            100, "Geodesic active contour complete.")

    def get_input_descriptions(self):
        return ('Feature image (ITK)', 'Initial level set (ITK)' )

    def set_input(self, idx, inputStream):
        try:
            if idx == 0:
                self._geodesicActiveContour.SetFeatureImage(inputStream)
            else:
                self._geodesicActiveContour.SetInput(inputStream)

        except TypeError, e:
            feat = self._geodesicActiveContour.GetFeatureImage()
            inp_img = self._geodesicActiveContour.GetInput()

            # deduce the type
            itku = itk_kit.utils
            ss = itku.get_img_type_and_dim_shortstring(inputStream)

            # either the other input has to be None, or match the type of the new input
            if idx == 0:
                if inp_img is not None:
                    other_ss = itku.get_img_type_and_dim_shortstring(inp_img)
                    if other_ss != ss:
                        raise TypeError('Types of feature image and initial level set have to match.')
            else:
                if feat is not None:
                    other_ss = itku.get_img_type_and_dim_shortstring(feat)
                    if other_ss != ss:
                        raise TypeError('Types of feature image and initial level set have to match.')

            img_type = getattr(itk.Image,ss)
            # try to build a new pipeline (will throw exception if it
            # can't)
            self._create_pipeline(img_type)

            # re-apply config
            self.sync_module_logic_with_config()
            # connect everything up
            if idx == 0:
                self._geodesicActiveContour.SetFeatureImage(inputStream)
                self._geodesicActiveContour.SetInput(inp_img)
            else:
                self._geodesicActiveContour.SetFeatureImage(feat)
                self._geodesicActiveContour.SetInput(inputStream)

    def get_output_descriptions(self):
        return ('Final level set (ITK Float 3D)',)

    def get_output(self, idx):
        return self._geodesicActiveContour.GetOutput()

    def config_to_logic(self):
        self._geodesicActiveContour.SetPropagationScaling(
            self._config.propagationScaling)

        self._geodesicActiveContour.SetCurvatureScaling(
            self._config.curvatureScaling)

        self._geodesicActiveContour.SetAdvectionScaling(
            self._config.advectionScaling)

        self._geodesicActiveContour.SetNumberOfIterations(
            self._config.numberOfIterations)

    def logic_to_config(self):
        self._config.propagationScaling = self._geodesicActiveContour.\
                                          GetPropagationScaling()

        self._config.curvatureScaling = self._geodesicActiveContour.\
                                        GetCurvatureScaling()

        self._config.advectionScaling = self._geodesicActiveContour.\
                                        GetAdvectionScaling()

        self._config.numberOfIterations = self._geodesicActiveContour.\
                                          GetNumberOfIterations()

    # --------------------------------------------------------------------
    # END OF API CALLS
    # --------------------------------------------------------------------

    def _create_pipeline(self, img_type):
        try:
            g = \
                itk.GeodesicActiveContourLevelSetImageFilter[
                        img_type,img_type,itk.F].New()
        except KeyError, e:
            emsg = 'Could not create GAC filter with input type %s. '\
                    'Please try a different input type.' % (ss,)
            raise TypeError, emsg

        # if successful, we can disconnect the old filter and store 
        # the instance (needed for the progress call!)
        if self._geodesicActiveContour:
            self._geodesicActiveContour.SetInput(None)

        self._geodesicActiveContour = g

        itk_kit.utils.setupITKObjectProgress(
            self, self._geodesicActiveContour,
            'GeodesicActiveContourLevelSetImageFilter',
            'Growing active contour')
        
    def _destroyITKPipeline(self):
        """Delete all bindings to components of the ITK pipeline.
        """

        del self._geodesicActiveContour
        
