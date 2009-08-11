# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

import itk
import module_kits.itk_kit as itk_kit
from module_base import ModuleBase
from module_mixins import ScriptedConfigModuleMixin

class cannyEdgeDetection(ScriptedConfigModuleMixin, ModuleBase):
    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        self._config.variance = (0.7, 0.7, 0.7)
        self._config.maximum_error = (0.01, 0.01, 0.01)
        self._config.upper_threshold = 0.0
        self._config.lower_threshold = 0.0
        self._config.outside_value = 0.0

        configList = [
            ('Variance:', 'variance', 'tuple:float,3', 'text',
             'Variance of Gaussian used for smoothing the input image (units: '
             'true spacing).'),
            ('Maximum error:', 'maximum_error', 'tuple:float,3', 'text',
             'The discrete Gaussian kernel will be sized so that the '
             'truncation error is smaller than this.'),
            ('Upper threshold:', 'upper_threshold', 'base:float', 'text',
             'Highest allowed value in the output image.'),
            ('Lower threshold:', 'lower_threshold', 'base:float', 'text',
             'Lowest allowed value in the output image.'),
            ('Outside value:', 'outside_value', 'base:float', 'text',
             'Pixels lower than threshold will be set to this.')]
        
        # setup the pipeline
        if3 = itk.Image[itk.F, 3]
        self._canny = itk.CannyEdgeDetectionImageFilter[if3, if3].New()
        
        itk_kit.utils.setupITKObjectProgress(
            self, self._canny, 'itkCannyEdgeDetectionImageFilter',
            'Performing Canny edge detection')

        ScriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self})
            
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
        del self._canny

    def execute_module(self):
        # create a new canny filter
        if3 = itk.Image.F3
        c = itk.CannyEdgeDetectionImageFilter[if3, if3].New()
        c.SetInput(self._canny.GetInput())

        # disconnect the old one
        self._canny.SetInput(None)
        # replace it with the new one
        self._canny = c

        # setup new progress handler
        itk_kit.utils.setupITKObjectProgress(
            self, self._canny, 'itkCannyEdgeDetectionImageFilter',
            'Performing Canny edge detection')

        # apply our config
        self.sync_module_logic_with_config()
      
        # and go!
        self._canny.Update()

    def get_input_descriptions(self):
        return ('ITK Image (3D, float)',)

    def set_input(self, idx, inputStream):
        self._canny.SetInput(inputStream)

    def get_output_descriptions(self):
        return ('ITK Edge Image (3D, float)',)

    def get_output(self, idx):
        return self._canny.GetOutput()

    def config_to_logic(self):
        # thanks to WrapITK, we can now set / get tuples / lists!

        # VARIANCE
        self._canny.SetVariance(self._config.variance)

        # MAXIMUM ERROR
        self._canny.SetMaximumError(self._config.maximum_error)

        # THRESHOLD
        self._canny.SetUpperThreshold(self._config.upper_threshold)
        self._canny.SetLowerThreshold(self._config.lower_threshold)

        # OUTSIDE VALUE
        self._canny.SetOutsideValue(self._config.outside_value)

    def logic_to_config(self):
        # VARIANCE
        self._config.variance = tuple(self._canny.GetVariance())

        # MAXIMUM ERROR
        self._config.maximum_error = \
            tuple(self._canny.GetMaximumError())

        # THRESHOLDS
        self._config.upper_threshold = self._canny.GetUpperThreshold()
        self._config.lower_threshold = self._canny.GetLowerThreshold()

        # OUTSIDE VALUE
        self._config.outside_value = self._canny.GetOutsideValue()
            
