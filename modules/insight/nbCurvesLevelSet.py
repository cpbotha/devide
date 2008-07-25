# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

import itk
import module_kits.itk_kit as itk_kit
from module_base import ModuleBase
from moduleMixins import scriptedConfigModuleMixin

class nbCurvesLevelSet(scriptedConfigModuleMixin, ModuleBase):

    def __init__(self, moduleManager):

        ModuleBase.__init__(self, moduleManager)
        
        # setup defaults
        self._config.propagationScaling = 1.0
        self._config.advectionScaling = 1.0
        self._config.curvatureScaling = 1.0
        self._config.numberOfIterations = 500
        
        configList = [
            ('Propagation scaling:', 'propagationScaling', 'base:float',
             'text', 'Weight factor for the propagation term'),
            ('Advection scaling:', 'advectionScaling', 'base:float',
             'text', 'Weight factor for the advection term'),
            ('Curvature scaling:', 'curvatureScaling', 'base:float',
             'text', 'Weight factor for the curvature term'),
            ('Number of iterations:', 'numberOfIterations', 'base:int',
             'text',
             'Number of iterations that the algorithm should be run for')]
        
        scriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self})

        # create all pipeline thingies
        self._createITKPipeline()

        self.sync_module_logic_with_config()
        
    def close(self):
        self._destroyITKPipeline()
        scriptedConfigModuleMixin.close(self)
        ModuleBase.close(self)

    def execute_module(self):
        self.get_output(0).Update()

    def get_input_descriptions(self):
        return ('Feature image (ITK)', 'Initial level set (ITK)' )

    def set_input(self, idx, inputStream):
        if idx == 0:
            self._nbcLS.SetFeatureImage(inputStream)
            
        else:
            self._nbcLS.SetInput(inputStream)
            

    def get_output_descriptions(self):
        return ('Image Data (ITK)',)

    def get_output(self, idx):
        return self._nbcLS.GetOutput()

    def config_to_logic(self):
        self._nbcLS.SetPropagationScaling(
            self._config.propagationScaling)

        self._nbcLS.SetAdvectionScaling(
            self._config.advectionScaling)

        self._nbcLS.SetCurvatureScaling(
            self._config.curvatureScaling)

    def logic_to_config(self):
        self._config.propagationScaling = self._nbcLS.\
                                          GetPropagationScaling()

        self._config.advectionScaling = self._nbcLS.GetAdvectionScaling()

        self._config.curvatureScaling = self._nbcLS.GetCurvatureScaling()

    # --------------------------------------------------------------------
    # END OF API CALLS
    # --------------------------------------------------------------------

    def _createITKPipeline(self):
        # input: smoothing.SetInput()
        # output: thresholder.GetOutput()

        if3 = itk.Image[itk.F, 3]
        self._nbcLS = itk.NarrowBandCurvesLevelSetImageFilter[if3,if3].New()
        #self._nbcLS.SetMaximumRMSError( 0.1 );
        self._nbcLS.SetNumberOfIterations( 500 );

        itk_kit.utils.setupITKObjectProgress(
            self, self._nbcLS,
            'NarrowBandCurvesLevelSetImageFilter',
            'Evolving level set')

        
    def _destroyITKPipeline(self):
        """Delete all bindings to components of the ITK pipeline.
        """

        del self._nbcLS
        
