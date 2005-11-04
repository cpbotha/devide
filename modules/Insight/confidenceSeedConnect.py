# $Id: confidenceSeedConnect.py,v 1.6 2005/11/04 10:34:55 cpbotha Exp $

import fixitk as itk
import genUtils
from moduleBase import moduleBase
import moduleUtils
import moduleUtilsITK
from moduleMixins import scriptedConfigModuleMixin

class confidenceSeedConnect(scriptedConfigModuleMixin, moduleBase):
    """Confidence-based 3D region growing.

    This module will perform a 3D region growing starting from the
    user-supplied points.  The mean and standard deviation are calculated in a
    small initial region around the seed points.  New contiguous points have
    to have intensities on the range [mean - f*stdDev, mean + f*stdDev] to be
    included.  f is user-definable.

    After this initial growing iteration, if the user has specified a larger
    than 0 number of iterations, the mean and standard deviation are
    recalculated over all the currently selected points and the process is
    restarted.  This process is repeated for the user-defined number of
    iterations, or until now new pixels are added.

    Due to weirdness in the underlying ITK filter, deleting all points
    won't quite work.  In other words, the output of this module can
    only be trusted if there's at least a single seed point.
    
    $Revision: 1.6 $
    """
    
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
        
        # setup the pipeline
        self._cCIF = itk.itkConfidenceConnectedImageFilterF3F3_New()
        
        moduleUtilsITK.setupITKObjectProgress(
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
                    
                # REMEMBER: if _inputPoints is an empty array (which can often
                # happen) the test "if self._inputPoints" will be false!  So,
                # check explicitly for != None.
                if self._inputPoints != None:
                    self._inputPoints.removeObserver(
                        self._observerInputPoints)

                self._inputPoints = inputStream
                
                if self._inputPoints:
                    self._inputPoints.addObserver(self._observerInputPoints)
                    self._transferPoints()
            

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
                                          
    def _observerInputPoints(self, obj):
        # this will be called if anything happens to the points
        self._transferPoints()

    def _transferPoints(self):
        """This will transfer all points from self._inputPoints to the nbhCIF
        instance.
        """

        self._cCIF.ClearSeeds()
        # it seems that ClearSeeds() doesn't call Modified(), so we do this
        # this is important if the list of inputPoints is empty.
        self._cCIF.Modified()
        
        for ip in self._inputPoints:
            # bugger, it could be that our input dataset has an extent
            # that doesn't start at 0,0,0... ITK doesn't understand this
            x,y,z = [int(i) for i in ip['discrete']]
            idx = itk.itkIndex3()
            idx.SetElement(0, x)
            idx.SetElement(1, y)
            idx.SetElement(2, z)
            self._cCIF.AddSeed(idx)
            
            print "Added %d,%d,%d" % (x,y,z)
