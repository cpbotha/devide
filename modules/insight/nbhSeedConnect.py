# $Id$

import itk
import module_kits.itk_kit as itk_kit
from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin

class nbhSeedConnect(scriptedConfigModuleMixin, moduleBase):
    
    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        # floats
        self._config.lower = 128.0
        self._config.upper = 255.0
        # segmented pixels will be replaced with this value
        self._config.replaceValue = 1.0
        # size of neighbourhood around candidate pixel
        self._config.radius = (1, 1, 1)
        
        configList = [
            ('Lower threshold:', 'lower', 'base:float', 'text',
             'Pixels have to have an intensity equal to or higher than '
             'this.'),
            ('Higher threshold:', 'upper', 'base:float', 'text',
             'Pixels have to have an intensity equal to or lower than this.'),
            ('Replace value:', 'replaceValue', 'base:float', 'text',
             'Segmented pixels will be assigned this value.'),
            ('Neighbourhood size:', 'radius', 'tuple:int,3', 'text',
             '3D integer radii of neighbourhood around candidate pixel.')]
            
        


        # this will contain our binding to the input points
        self._inputPoints = None
        
        # setup the pipeline
        if3 = itk.Image[itk.F, 3]
        self._nbhCIF = itk.NeighborhoodConnectedImageFilter[if3,if3].New()
        
        itk_kit.utils.setupITKObjectProgress(
            self, self._nbhCIF, 'itkNeighborhoodConnectedImageFilter',
            'Region growing...')

        scriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
             'itkNeighborhoodConnectedImageFilter' : self._nbhCIF})

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
        del self._nbhCIF

    def execute_module(self):
        self._transferPoints()
        self._nbhCIF.Update()

    def get_input_descriptions(self):
        return ('ITK Image (3D, float)', 'Seed points')

    def set_input(self, idx, inputStream):
        if idx == 0:
            self._nbhCIF.SetInput(inputStream)

        else:
            if inputStream != self._inputPoints:
                self._inputPoints = inputStream
            

    def get_output_descriptions(self):
        return ('Segmented ITK Image (3D, float)',)

    def get_output(self, idx):
        return self._nbhCIF.GetOutput()

    def config_to_logic(self):
        self._nbhCIF.SetLower(self._config.lower)
        self._nbhCIF.SetUpper(self._config.upper)
        self._nbhCIF.SetReplaceValue(self._config.replaceValue)

        # now setup the radius
        sz = self._nbhCIF.GetRadius()
        sz.SetElement(0, self._config.radius[0])
        sz.SetElement(1, self._config.radius[1])
        sz.SetElement(2, self._config.radius[2])
        self._nbhCIF.SetRadius(sz)

    def logic_to_config(self):
        self._config.lower = self._nbhCIF.GetLower()
        self._config.upper = self._nbhCIF.GetUpper()
        self._config.replaceValue = self._nbhCIF.GetReplaceValue()

        sz = self._nbhCIF.GetRadius()
        self._config.radius = tuple(
            (sz.GetElement(0), sz.GetElement(1), sz.GetElement(2)))

                                          
    def _transferPoints(self):
        """This will transfer all points from self._inputPoints to the nbhCIF
        instance.
        """

        # SetSeed calls ClearSeeds and then AddSeed
        self._nbhCIF.ClearSeeds()
        if len(self._inputPoints) > 0:
            for ip in self._inputPoints:
                # bugger, it could be that our input dataset has an extent
                # that doesn't start at 0,0,0... ITK doesn't understand this

                # we have to cast these to int... they are discrete,
                # but the IPW seems to be returning them as floats
                x,y,z = [int(i) for i in ip['discrete']]
                idx = itk.Index[3]()
                idx.SetElement(0, x)
                idx.SetElement(1, y)
                idx.SetElement(2, z)
                self._nbhCIF.AddSeed(idx)
                print "Added %d,%d,%d" % (x,y,z)

                
                
            
            
