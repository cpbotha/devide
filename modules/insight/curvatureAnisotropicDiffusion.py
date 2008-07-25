# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

import itk
import module_kits.itk_kit as itk_kit
from module_base import ModuleBase
from moduleMixins import scriptedConfigModuleMixin

class curvatureAnisotropicDiffusion(scriptedConfigModuleMixin, ModuleBase):

    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        self._config.numberOfIterations = 5
        self._config.conductanceParameter = 3.0

        configList = [
            ('Number of iterations:', 'numberOfIterations', 'base:int', 'text',
             'Number of time-step updates (iterations) the solver will '
             'perform.'),
            ('Conductance parameter:', 'conductanceParameter', 'base:float',
             'text', 'Sensitivity of the  conductance term.  Lower == more '
             'preservation of image features.')]

        



        # setup the pipeline
        if3 = itk.Image[itk.F, 3]
        d = itk.CurvatureAnisotropicDiffusionImageFilter[if3, if3].New()
        d.SetTimeStep(0.0625) # standard for 3D
        self._diffuse = d
        
        itk_kit.utils.setupITKObjectProgress(
            self, self._diffuse,
            'itkCurvatureAnisotropicDiffusionImageFilter',
            'Smoothing data')

        scriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
             'itkCurvatureAnisotropicDiffusion' : self._diffuse})

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
        del self._diffuse

    def execute_module(self):
        self._diffuse.Update()

    def get_input_descriptions(self):
        return ('ITK Image (3D, float)',)

    def set_input(self, idx, inputStream):
        self._diffuse.SetInput(inputStream)

    def get_output_descriptions(self):
        return ('ITK Image (3D, float)',)

    def get_output(self, idx):
        return self._diffuse.GetOutput()

    def config_to_logic(self):
        self._diffuse.SetNumberOfIterations(self._config.numberOfIterations)
        self._diffuse.SetConductanceParameter(
            self._config.conductanceParameter)

    def logic_to_config(self):
        self._config.numberOfIterations = self._diffuse.GetNumberOfIterations()
        self._config.conductanceParameter = self._diffuse.\
                                            GetConductanceParameter()
