# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

import itk
import module_kits.itk_kit as itk_kit
from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin

class cannyEdgeDetection(scriptedConfigModuleMixin, moduleBase):
    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        self._config.variance = (0.7, 0.7, 0.7)
        self._config.maximumError = (0.01, 0.01, 0.01)
        self._config.threshold = 0.0
        self._config.outsideValue = 0.0

        configList = [
            ('Variance:', 'variance', 'tuple:float,3', 'text',
             'Variance of Gaussian used for smoothing the input image (units: '
             'true spacing).'),
            ('Maximum error:', 'maximumError', 'tuple:float,3', 'text',
             'The discrete Gaussian kernel will be sized so that the '
             'truncation error is smaller than this.'),
            ('Threshold:', 'threshold', 'base:float', 'text',
             'Lowest allowed value in the output image.'),
            ('Outside value:', 'outsideValue', 'base:float', 'text',
             'Pixels lower than threshold will be set to this.')]
        



        # setup the pipeline
        if3 = itk.Image[itk.F, 3]
        self._canny = itk.CannyEdgeDetectionImageFilter[if3, if3].New()
        
        itk_kit.utils.setupITKObjectProgress(
            self, self._canny, 'itkCannyEdgeDetectionImageFilter',
            'Performing Canny edge detection')

        scriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
             'itkCannyEdgeDetectionImageFilter' : self._canny})
            
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
        del self._canny

    def execute_module(self):
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
        # VARIANCE
        var = self._canny.GetVariance()
        for i in range(3):
            var.SetElement(i, self._config.variance[i])

        self._canny.SetVariance(var)

        # MAXIMUM ERROR
        me = self._canny.GetMaximumError()
        for i in range(3):
            me.SetElement(i, self._config.maximumError[i])

        self._canny.SetMaximumError(me)

        # THRESHOLD
        self._canny.SetUpperThreshold(self._config.threshold)
        # this is to emulate the old behaviour where there was only
        # one threshold.
        # see: http://public.kitware.com/Bug/bug.php?op=show&bugid=1511
        # we'll bring these into the GUI later
        self._canny.SetLowerThreshold(self._config.threshold / 2.0)

        # OUTSIDE VALUE
        self._canny.SetOutsideValue(self._config.outsideValue)

    def logic_to_config(self):
        # Damnit!  This is returning mostly float parameters (instead of
        # double), so that str() in Python is having a hard time formatting
        # the things nicely.
        
        # VARIANCE
        var = self._canny.GetVariance()
        self._config.variance = (var.GetElement(0), var.GetElement(1),
                                 var.GetElement(2))

        # MAXIMUM ERROR
        me = self._canny.GetMaximumError()
        self._config.maximumError = (me.GetElement(0), me.GetElement(1),
                                     me.GetElement(2))

        # THRESHOLD
        self._config.threshold = self._canny.GetUpperThreshold()

        # OUTSIDE VALUE
        self._config.outsideValue = self._canny.GetOutsideValue()
            
