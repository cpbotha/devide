# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

import itk
import module_kits.itk_kit as itk_kit
from module_base import ModuleBase
from moduleMixins import scriptedConfigModuleMixin

class gaussianConvolve(scriptedConfigModuleMixin, ModuleBase):

    _orders = ['Zero', 'First', 'Second']
    
    def __init__(self, moduleManager):
        ModuleBase.__init__(self, moduleManager)

        self._config.direction = 0
        self._config.sigma = 1.0
        self._config.order = 'Zero'
        self._config.normaliseAcrossScale = False        
        
        configList = [
            ('Direction:', 'direction', 'base:int', 'choice',
             'Direction in which the filter has to be applied.',
             ['0', '1', '2']),
            ('Sigma:', 'sigma', 'base:float', 'text',
             'Sigma of Gaussian kernel in world coordinates.'),

            ('Order of Gaussian', 'order', 'base:str', 'choice',
             'Convolve with Gaussian, or first or second derivative.',
             tuple(self._orders)),
            ('Normalise across scale', 'normaliseAcrossScale', 'base:bool',
             'checkbox', 'Determine and use normalisation factor.')]
        



        # setup the pipeline
        if3 = itk.Image[itk.F, 3]
        self._gaussian = itk.RecursiveGaussianImageFilter[if3,if3].New()
        
        itk_kit.utils.setupITKObjectProgress(
            self, self._gaussian, 'itkRecursiveGaussianImageFilter',
            'Convolving with Gaussian')

        scriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
             'itkRecursiveGaussianImageFilter' : self._gaussian})

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
        del self._gaussian

    def execute_module(self):
        self._gaussian.Update()

    def get_input_descriptions(self):
        return ('ITK Image (3D, float)',)

    def set_input(self, idx, inputStream):
        self._gaussian.SetInput(inputStream)

    def get_output_descriptions(self):
        return ('Blurred ITK Image (3D, float)',)

    def get_output(self, idx):
        return self._gaussian.GetOutput()

    def config_to_logic(self):
        self._gaussian.SetDirection(self._config.direction)
        
        # SIGMA
        self._gaussian.SetSigma(self._config.sigma)

        # ORDER
        if self._config.order == 'Zero':
            self._gaussian.SetZeroOrder()
        elif self._config.order == 'First':
            self._gaussian.SetFirstOrder()
        elif self._config.order == 'Second':
            self._gaussian.SetSecondOrder()
        else:
            self._config.order = 'Zero'
            self._gaussian.SetZeroOrder()
        
        # NORMALISEACROSSSCALE
        self._gaussian.SetNormalizeAcrossScale(
            self._config.normaliseAcrossScale)
        

    def logic_to_config(self):
        self._config.direction = self._gaussian.GetDirection()
        
        # SIGMA
        self._config.sigma = self._gaussian.GetSigma()

        # ORDER
        # FIMXE: dammit, we can't get the order.

        # NORMALISEACROSSSCALE
        self._config.normaliseAcrossScale = self._gaussian.\
                                            GetNormalizeAcrossScale()
