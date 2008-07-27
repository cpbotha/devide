# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

import itk
import module_kits.itk_kit as itk_kit
import gen_utils
from module_base import ModuleBase
from module_mixins import ScriptedConfigModuleMixin

class confidenceSeedConnect(ScriptedConfigModuleMixin, ModuleBase):
    
    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        # setup config thingy
        self._config.multiplier = 2.5
        self._config.numberOfIterations = 4
        # segmented pixels will be replaced with this value
        self._config.replaceValue = 1.0
        # size of neighbourhood around candidate pixel
        self._config.initialRadius = 1
        
        configList = [
            ('Multiplier (f):', 'multiplier', 'base:float', 'text',
             'Multiplier for the standard deviation term.'),
            ('Initial neighbourhood:', 'initialRadius', 'base:int', 'text',
             'The radius (in pixels) of the initial region.'),
            ('Number of Iterations:', 'numberOfIterations', 'base:int', 'text',
             'The region will be expanded so many times.'),
            ('Replace value:', 'replaceValue', 'base:float', 'text',
             'Segmented pixels will be assigned this value.')]
        


        # this will contain our binding to the input points
        self._inputPoints = None
        # and this will be our internal list
        self._seedPoints = []
        
        # setup the pipeline
        if3 = itk.Image[itk.F, 3]
        self._cCIF = itk.ConfidenceConnectedImageFilter[if3, if3].New()
        
        itk_kit.utils.setupITKObjectProgress(
            self, self._cCIF, 'itkConfidenceConnectedImageFilter',
            'Region growing...')

        ScriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
             'itkConfidenceConnectedImageFilter' : self._cCIF})
            
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
        del self._cCIF

    def execute_module(self):
        self._transferPoints()
        self._cCIF.Update()

    def get_input_descriptions(self):
        return ('ITK Image (3D, float)', 'Seed points')

    def set_input(self, idx, inputStream):
        if idx == 0:
            self._cCIF.SetInput(inputStream)

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
        return ('Segmented ITK Image (3D, float)',)

    def get_output(self, idx):
        return self._cCIF.GetOutput()

    def config_to_logic(self):
        self._cCIF.SetMultiplier(self._config.multiplier)
        self._cCIF.SetInitialNeighborhoodRadius(self._config.initialRadius)
        self._cCIF.SetNumberOfIterations(self._config.numberOfIterations)
        self._cCIF.SetReplaceValue(self._config.replaceValue)

    def logic_to_config(self):
        self._config.multiplier = self._cCIF.GetMultiplier()
        self._config.initialRadius = self._cCIF.GetInitialNeighborhoodRadius()
        self._config.numberOfIterations = self._cCIF.GetNumberOfIterations()
        self._config.replaceValue = self._cCIF.GetReplaceValue()
                                          
    def _transferPoints(self):
        """This will transfer all points from self._inputPoints to the nbhCIF
        instance.
        """

        # extract a list from the input points
        tempList = []
        if self._inputPoints:
            for i in self._inputPoints:
                tempList.append(i['discrete'])

        if tempList != self._seedPoints:
            self._seedPoints = tempList
        

            self._cCIF.ClearSeeds()
            # it seems that ClearSeeds() doesn't call Modified(), so we do this
            # this is important if the list of inputPoints is empty.
            self._cCIF.Modified()
        
            for ip in self._seedPoints:
                # bugger, it could be that our input dataset has an extent
                # that doesn't start at 0,0,0... ITK doesn't understand this
                x,y,z = [int(i) for i in ip]
                idx = itk.Index[3]()
                idx.SetElement(0, x)
                idx.SetElement(1, y)
                idx.SetElement(2, z)
                self._cCIF.AddSeed(idx)
            
                print "Added %d,%d,%d" % (x,y,z)
