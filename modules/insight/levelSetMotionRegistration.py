# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

import itk
import module_kits.itk_kit as itk_kit
from module_base import ModuleBase
from moduleMixins import scriptedConfigModuleMixin

class levelSetMotionRegistration(scriptedConfigModuleMixin, ModuleBase):
    def __init__(self, module_manager):
        
        ModuleBase.__init__(self, module_manager)

        self._config.numberOfIterations = 50
        self._config.gradSmoothStd = 1.0
        self._config.alpha = 0.1
        self._config.idiffThresh = 0.001

        configList = [
            ('Number of iterations:', 'numberOfIterations',
             'base:int', 'text',
             'Number of iterations for the Demons registration to run.'),
            ('Gradient smoothing standard deviation:', 'gradSmoothStd',
             'base:float', 'text',
             'The standard deviation of the Gaussian kernel in physical '
             'units that will be '
             'used to smooth the images before calculating gradients.'),
            ('Stability parameter alpha:', 'alpha', 'base:float', 'text',
             'Used to stabilise small gradient magnitude values.  Set to '
             'approximately 0.04% of intensity range of input images.'),
            ('Intensity difference threshold:', 'idiffThresh',
             'base:float', 'text',
             'Voxels differing with less than this threshold are considered '
             'equal')]



        # input 1 is fixed, input 2 is moving
        # matcher.SetInput(moving)
        # matcher.SetReferenceImage(fixed)

        if3 = itk.Image.F3
        
        self._matcher = itk.HistogramMatchingImageFilter[if3,if3].New()
        self._matcher.SetNumberOfHistogramLevels(1024)
        self._matcher.SetNumberOfMatchPoints(7)
        self._matcher.ThresholdAtMeanIntensityOn()

        ivf3 = itk.Image.VF33
        ls = itk.LevelSetMotionRegistrationFilter[if3, if3, ivf3].New()
        self._levelSetMotion = ls
                             
        self._levelSetMotion.SetMovingImage(self._matcher.GetOutput())

        # we should get a hold of GetElapsedIterations...
        # DenseFiniteDifference -> PDEDeformableRegistration -> LevelSetMotion
        # Dense still has it, PDE onwards doesn't.  Dense is templated on
        # input and output, PDE on two image types and a deformation field...
        itk_kit.utils.setupITKObjectProgress(
            self, self._levelSetMotion, 'LevelSetMotionRegistrationFilter',
            'Performing registration, metric = %.2f',
            ('GetMetric()',))

        scriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
             'LevelSetMotionRegistrationFilter' : self._levelSetMotion,
             'itkHistogramMatchingImageFilter' : self._matcher})

        self.sync_module_logic_with_config()
        
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
        del self._levelSetMotion
        del self._matcher

    def execute_module(self):
        self.get_output(0).Update()

    def get_input_descriptions(self):
        return ('Fixed image (ITK 3D Float)', 'Moving image (ITK 3D Float)')

    def set_input(self, idx, inputStream):
        if idx == 0:
            self._matcher.SetReferenceImage(inputStream)
            self._levelSetMotion.SetFixedImage(inputStream)

        else:
            self._matcher.SetInput(inputStream)
        
    def get_output_descriptions(self):
        return ('Deformation field (ITK 3D Float vectors)',)

    def get_output(self, idx):
        return self._levelSetMotion.GetOutput()

    def config_to_logic(self):
        self._levelSetMotion.SetNumberOfIterations(
            self._config.numberOfIterations)
        self._levelSetMotion.SetGradientSmoothingStandardDeviations(
            self._config.gradSmoothStd)
        self._levelSetMotion.SetAlpha(self._config.alpha)
        self._levelSetMotion.SetIntensityDifferenceThreshold(
            self._config.idiffThresh)

    def logic_to_config(self):
        self._config.numberOfIterations = self._levelSetMotion.\
                                          GetNumberOfIterations()
        
        self._config.gradSmoothStd = \
                                   self._levelSetMotion.\
                                   GetGradientSmoothingStandardDeviations()

        self._config.alpha = \
                           self._levelSetMotion.GetAlpha()
        
        self._config.idiffThresh = \
                                 self._levelSetMotion.\
                                 GetIntensityDifferenceThreshold()
        

    
        
