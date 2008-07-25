# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

import itk
import module_kits.itk_kit as itk_kit
from module_base import ModuleBase
from module_mixins import ScriptedConfigModuleMixin

class tpgac(ScriptedConfigModuleMixin, ModuleBase):


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
        self._createITKPipeline()

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
        if idx == 0:
            self._tpgac.SetFeatureImage(inputStream)
            
        else:
            self._tpgac.SetInput(inputStream)
            

    def get_output_descriptions(self):
        return ('Final level set (ITK Float 3D)',)

    def get_output(self, idx):
        return self._tpgac.GetOutput()

    def config_to_logic(self):
        self._tpgac.SetPropagationScaling(
            self._config.propagationScaling)

        self._tpgac.SetCurvatureScaling(
            self._config.curvatureScaling)

        self._tpgac.SetAdvectionScaling(
            self._config.advectionScaling)

        self._tpgac.SetNumberOfIterations(
            self._config.numberOfIterations)

    def logic_to_config(self):
        self._config.propagationScaling = self._tpgac.\
                                          GetPropagationScaling()

        self._config.curvatureScaling = self._tpgac.\
                                        GetCurvatureScaling()

        self._config.advectionScaling = self._tpgac.\
                                        GetAdvectionScaling()

        self._config.numberOfIterations = self._tpgac.\
                                          GetNumberOfIterations()

    # --------------------------------------------------------------------
    # END OF API CALLS
    # --------------------------------------------------------------------

    def _createITKPipeline(self):
        # input: smoothing.SetInput()
        # output: thresholder.GetOutput()

        if3 = itk.Image.F3
        self._tpgac = itk.TPGACLevelSetImageFilter[if3, if3, itk.F].New()
        #geodesicActiveContour.SetMaximumRMSError( 0.1 );

        itk_kit.utils.setupITKObjectProgress(
            self, self._tpgac,
            'TPGACLevelSetImageFilter',
            'Growing active contour')
        
    def _destroyITKPipeline(self):
        """Delete all bindings to components of the ITK pipeline.
        """

        del self._tpgac
        
