# $Id: fastMarching.py,v 1.1 2004/04/27 09:22:59 cpbotha Exp $

import fixitk as itk
import genUtils
from moduleBase import moduleBase
import moduleUtils
import moduleUtilsITK
from moduleMixins import scriptedConfigModuleMixin

class fastMarching(scriptedConfigModuleMixin, moduleBase):
    """Given a set of seed points and a speed image, this module will
    propagate a moving front out from those points using the fast marching
    level set formulation.

    $Revision: 1.1 $
    """

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        # setup config thingy
        self._config.stoppingValue = 256
        self._config.normalisationFactor = 1.0

        configList = [
            ('Stoping value:', 'stoppingValue', 'base:float', 'text',
             'When an arrival time is greater than the stopping value, the '
             'algorithm terminates.'),
            ('Normalisation factor:', 'normalisationFactor', 'base:int',
             'text',
             'Values in the speed image are divide by this factor.')]
        
        scriptedConfigModuleMixin.__init__(self, configList)

        # this will contain our binding to the input points
        self._inputPoints = None
        
        # setup the pipeline
        self._fastMarching = itk.itkFastMarchingImageFilterF3F3_New()
        
        moduleUtilsITK.setupITKObjectProgress(
            self, self._fastMarching, 'itkFastMarchingImageFilter',
            'Propagating front.')

        self._createWindow(
            {'Module (self)' : self,
             'itkFastMarchingImageFilter' : self._fastMarching})

        self.configToLogic()
        self.syncViewWithLogic()

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
                    
                
                if self._inputPoints:
                    self._inputPoints.removeObserver(
                        self._observerInputPoints)

                self._inputPoints = inputStream
                
                if self._inputPoints:
                    self._inputPoints.addObserver(self._observerInputPoints)
                    self._transferPoints()
            

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
                                          
    def _observerInputPoints(self, obj):
        # this will be called if anything happens to the points
        self._transferPoints()

    def _transferPoints(self):
        """This will transfer all points from self._inputPoints to the
        _fastMarching object.
        """

        if len(self._inputPoints) > 0:

            seeds = itk.itkNodeContainerF3_New()
            seeds.Initialize()
            
            for ip,i in zip(self._inputPoints,
                            range(len(self._inputPoints))):
                # bugger, it could be that our input dataset has an extent
                # that doesn't start at 0,0,0... ITK doesn't understand this
                x,y,z = [int(i) for i in ip['discrete']]

                idx = itk.itkIndex3()
                idx.SetElement(0, x)
                idx.SetElement(1, y)
                idx.SetElement(2, z)

                node = itk.itkLevelSetNodeF3()
                node.SetValue(0)
                node.SetIndex(idx)

                seeds.InsertElement(i, node)

                self._fastMarching.SetTrialPoints(seeds.GetPointer())

                print "Added %d,%d,%d" % (x,y,z)

    
