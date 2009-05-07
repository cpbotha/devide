# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

import itk
import module_kits.itk_kit as itk_kit
from module_base import ModuleBase
from module_mixins import ScriptedConfigModuleMixin

class fastMarching(ScriptedConfigModuleMixin, ModuleBase):
    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        # setup config thingy
        self._config.stoppingValue = 256
        self._config.normalisationFactor = 1.0
        self._config.initial_distance = 0

        configList = [
            ('Stopping value:', 'stoppingValue', 'base:float', 'text',
             'When an arrival time is greater than the stopping value, the '
             'algorithm terminates.'),
            ('Normalisation factor:', 'normalisationFactor',
                'base:float', 'text',
             'Values in the speed image are divide by this factor.'),
            ('Initial distance:', 'initial_distance', 'base:int', 'text',
             'Initial distance of fast marching seed points.')]
        


        # this will contain our binding to the input points
        self._inputPoints = None
        
        # setup the pipeline
        if3 = itk.Image.F3
        self._fastMarching = itk.FastMarchingImageFilter[if3,if3].New()
        
        itk_kit.utils.setupITKObjectProgress(
            self, self._fastMarching, 'itkFastMarchingImageFilter',
            'Propagating front.')

        ScriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
             'itkFastMarchingImageFilter' : self._fastMarching})
            
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
        del self._fastMarching

    def execute_module(self):
        self._transferPoints()
        self._fastMarching.Update()

    def get_input_descriptions(self):
        return ('Speed image (ITK, 3D, float)', 'Seed points')

    def set_input(self, idx, inputStream):
        if idx == 0:
            self._fastMarching.SetInput(inputStream)

        else:
            if inputStream != self._inputPoints:
                # check that the inputStream is either None (meaning
                # disconnect) or a valid type

                try:
                    if inputStream != None and \
                       inputStream.devideType != 'namedPoints':
                        raise TypeError

                except (AttributeError, TypeError):
                    raise TypeError, 'This input requires a points-type'
                    
                self._inputPoints = inputStream
                
    def get_output_descriptions(self):
        return ('Front arrival times (ITK, 3D, float)',)

    def get_output(self, idx):
        return self._fastMarching.GetOutput()

    def config_to_logic(self):
        self._fastMarching.SetStoppingValue(self._config.stoppingValue)
        self._fastMarching.SetNormalizationFactor(
            self._config.normalisationFactor)

    def logic_to_config(self):
        self._config.stoppingValue = self._fastMarching.GetStoppingValue()
        self._config.normalisationFactor = self._fastMarching.\
                                           GetNormalizationFactor()
                                          
    def _transferPoints(self):
        """This will transfer all points from self._inputPoints to the
        _fastMarching object.
        """

        if len(self._inputPoints) > 0:


            # get list of discrete coordinates
            dcoords = [p['discrete'] for p in self._inputPoints]

            # use utility function to convert these to vector
            # container
            seeds = \
                itk_kit.utils.coordinates_to_vector_container(
                        dcoords, self._config.initial_distance)

            self._fastMarching.SetTrialPoints(seeds)



    
