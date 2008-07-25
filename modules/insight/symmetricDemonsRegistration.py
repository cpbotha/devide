# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

import itk
import module_kits.itk_kit as itk_kit
from module_base import ModuleBase
from module_mixins import ScriptedConfigModuleMixin

class symmetricDemonsRegistration(ScriptedConfigModuleMixin, ModuleBase):
    def __init__(self, module_manager):
        
        ModuleBase.__init__(self, module_manager)

        self._config.numberOfIterations = 50
        self._config.deformationSmoothingStd = 1.0
        self._config.idiffThresh = 0.001

        configList = [
            ('Number of iterations:', 'numberOfIterations',
             'base:int', 'text',
             'Number of iterations for the Demons registration to run.'),
            ('Standard deviation of vector smoothing:',
             'deformationSmoothingStd', 'base:float', 'text',
             'Standard deviation of Gaussian kernel used to smooth '
             'intermediate deformation field'),            
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

        self._demons = itk.SymmetricForcesDemonsRegistrationFilter[
            itk.Image.F3, itk.Image.F3, itk.Image.VF33].New()
        self._demons.SetStandardDeviations(1.0)
        self._demons.SetMovingImage(self._matcher.GetOutput())

        itk_kit.utils.setupITKObjectProgress(
            self, self._demons, 'itkSymmetricForcesDemonsRegistration',
            'Performing registration, metric = %.2f', ('GetMetric()',))

        ScriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
             'itkSymmetricForcesDemonsRegistrationFilter' : self._demons,
             'itkHistogramMatchingImageFilter' : self._matcher})
        
        self.sync_module_logic_with_config()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        ScriptedConfigModuleMixin.close(self)
        # and the baseclass close
        ModuleBase.close(self)
            
        # remove all bindings
        del self._demons
        del self._matcher

    def execute_module(self):
        self.get_output(0).Update()

    def get_input_descriptions(self):
        return ('Fixed image (ITK 3D Float)', 'Moving image (ITK 3D Float)')

    def set_input(self, idx, inputStream):
        if idx == 0:
            self._matcher.SetReferenceImage(inputStream)
            self._demons.SetFixedImage(inputStream)

        else:
            self._matcher.SetInput(inputStream)
        
    def get_output_descriptions(self):
        return ('Deformation field (ITK 3D Float vectors)',)

    def get_output(self, idx):
        return self._demons.GetOutput()

    def config_to_logic(self):
        self._demons.SetNumberOfIterations(self._config.numberOfIterations)
        self._demons.SetStandardDeviations(
            self._config.deformationSmoothingStd)
        self._demons.SetIntensityDifferenceThreshold(
            self._config.idiffThresh)

    def logic_to_config(self):
        self._config.numberOfIterations = self._demons.GetNumberOfIterations()
        # we can't get the StandardDeviations back...
        self._config.idiffThresh = \
                                 self._demons.GetIntensityDifferenceThreshold()
        

    
        
