# $Id$

import itk
import module_kits.itk_kit as itk_kit
import genUtils
from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin

class confidenceSeedConnect(scriptedConfigModuleMixin, moduleBase):
    
    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

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
        
        scriptedConfigModuleMixin.__init__(self, configList)

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

        self._createWindow(
            {'Module (self)' : self,
             'itkConfidenceConnectedImageFilter' : self._cCIF})

        self.configToLogic()
        self.logicToConfig()
        self.configToView()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)
        # and the baseclass close
        moduleBase.close(self)
            
        # remove all bindings
        del self._cCIF

    def executeModule(self):
        self._transferPoints()
        self._cCIF.Update()

    def getInputDescriptions(self):
        return ('ITK Image (3D, float)', 'Seed points')

    def setInput(self, idx, inputStream):
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
                
    def getOutputDescriptions(self):
        return ('Segmented ITK Image (3D, float)',)

    def getOutput(self, idx):
        return self._cCIF.GetOutput()

    def configToLogic(self):
        self._cCIF.SetMultiplier(self._config.multiplier)
        self._cCIF.SetInitialNeighborhoodRadius(self._config.initialRadius)
        self._cCIF.SetNumberOfIterations(self._config.numberOfIterations)
        self._cCIF.SetReplaceValue(self._config.replaceValue)

    def logicToConfig(self):
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
