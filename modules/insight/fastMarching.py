# $Id$

import itk
import module_kits.itk_kit as itk_kit
from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin

class fastMarching(scriptedConfigModuleMixin, moduleBase):
    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        # setup config thingy
        self._config.stoppingValue = 256
        self._config.normalisationFactor = 1.0
        self._config.initial_distance = 0

        configList = [
            ('Stopping value:', 'stoppingValue', 'base:float', 'text',
             'When an arrival time is greater than the stopping value, the '
             'algorithm terminates.'),
            ('Normalisation factor:', 'normalisationFactor', 'base:int',
             'text',
             'Values in the speed image are divide by this factor.'),
            ('Initial distance:', 'initial_distance', 'base:int', 'text',
             'Initial distance of fast marching seed points.')]
        
        scriptedConfigModuleMixin.__init__(self, configList)

        # this will contain our binding to the input points
        self._inputPoints = None
        
        # setup the pipeline
        if3 = itk.Image.F3
        self._fastMarching = itk.FastMarchingImageFilter[if3,if3].New()
        
        itk_kit.utils.setupITKObjectProgress(
            self, self._fastMarching, 'itkFastMarchingImageFilter',
            'Propagating front.')

        self._createWindow(
            {'Module (self)' : self,
             'itkFastMarchingImageFilter' : self._fastMarching})

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
        del self._fastMarching

    def executeModule(self):
        self._transferPoints()
        self._fastMarching.Update()

    def getInputDescriptions(self):
        return ('Speed image (ITK, 3D, float)', 'Seed points')

    def setInput(self, idx, inputStream):
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
                
    def getOutputDescriptions(self):
        return ('Front arrival times (ITK, 3D, float)',)

    def getOutput(self, idx):
        return self._fastMarching.GetOutput()

    def configToLogic(self):
        self._fastMarching.SetStoppingValue(self._config.stoppingValue)
        self._fastMarching.SetNormalizationFactor(
            self._config.normalisationFactor)

    def logicToConfig(self):
        self._config.stoppingValue = self._fastMarching.GetStoppingValue()
        self._config.normalisationFactor = self._fastMarching.\
                                           GetNormalizationFactor()
                                          
    def _transferPoints(self):
        """This will transfer all points from self._inputPoints to the
        _fastMarching object.
        """

        if len(self._inputPoints) > 0:

            seeds = itk.VectorContainer[itk.UI,
                                        itk.LevelSetNode[itk.F, 3]].New()
            # this will clear it
            seeds.Initialize()

            for ip,nodePos in zip(self._inputPoints,
                                  range(len(self._inputPoints))):
                # bugger, it could be that our input dataset has an extent
                # that doesn't start at 0,0,0... ITK doesn't understand this
                x,y,z = [int(i) for i in ip['discrete']]

                idx = itk.Index[3]()
                idx.SetElement(0, x)
                idx.SetElement(1, y)
                idx.SetElement(2, z)

                node = itk.LevelSetNode[itk.F, 3]()
                node.SetValue(self._config.initial_distance)
                node.SetIndex(idx)

                seeds.InsertElement(nodePos, node)
                
                print "Added %d,%d,%d at %d" % (x,y,z,nodePos)

            self._fastMarching.SetTrialPoints(seeds)



    
