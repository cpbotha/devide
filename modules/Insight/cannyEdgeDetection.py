# $Id: cannyEdgeDetection.py,v 1.1 2004/03/22 13:56:01 cpbotha Exp $

import fixitk as itk
import genUtils
from moduleBase import moduleBase
import moduleUtils
import moduleUtilsITK
from moduleMixins import scriptedConfigModuleMixin

class cannyEdgeDetection(scriptedConfigModuleMixin, moduleBase):
    """Performs 3D Canny edge detection on input image.


    $Revision: 1.1 $
    """
    
    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        self._config.variance = (0.7, 0.7, 0.7)
        self._config.maximumError = (0.1, 0.1, 0.1)
        self._config.threshold = 0.0
        self._config.outsideValue = 0.0

        configList = [
            ('Variance:', 'variance', 'tuple:float,3', 'text',
             'Variance of Gaussian used for smoothing the input image (units: '
             'true spacing).'),
            ('Maximum error:', 'maximumError', 'tuple:float,3', 'text',
             'The discrete Gaussian kernel will be sized so that the '
             'truncation error is smaller than this.'),
            ('Threshold:', 'threshold', 'base:float', 'text',
             'Lowest allowed value in the output image.'),
            ('Outside value:', 'outsideValue', 'base:float', 'text',
             'Pixels lower than threshold will be set to this.')]
        
        scriptedConfigModuleMixin.__init__(self, configList)


        # setup the pipeline
        self._canny = itk.itkCannyEdgeDetectionImageFilterF3F3_New()
        
        moduleUtilsITK.setupITKObjectProgress(
            self, self._canny, 'itkCannyEdgeDetectionImageFilter',
            'Performing Canny edge detection')

        self._createWindow(
            {'Module (self)' : self,
             'itkCannyEdgeDetectionImageFilter' : self._canny})

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
        del self._canny

    def executeModule(self):
        self._canny.Update()

    def getInputDescriptions(self):
        return ('ITK Image (3D, float)',)

    def setInput(self, idx, inputStream):
        self._canny.SetInput(inputStream)

    def getOutputDescriptions(self):
        return ('ITK Edge Image (3D, float)',)

    def getOutput(self, idx):
        return self._canny.GetOutput()

    def configToLogic(self):
        # VARIANCE
        var = self._canny.GetVariance()
        for i in range(3):
            var.SetElement(i, self._config.variance[i])

        self._canny.SetVariance(var)

        # MAXIMUM ERROR
        me = self._canny.GetMaximumError()
        for i in range(3):
            me.SetElement(i, self._config.maximumError[i])

        self._canny.SetMaximumError(me)

        # THRESHOLD
        self._canny.SetThreshold(self._config.threshold)

        # OUTSIDE VALUE
        self._canny.SetOutsideValue(self._config.outsideValue)

    def logicToConfig(self):
        # Damnit!  This is returning mostly float parameters (instead of
        # double), so that str() in Python is having a hard time formatting
        # the things nicely.
        
        # VARIANCE
        var = self._canny.GetVariance()
        self._config.variance = (var.GetElement(0), var.GetElement(1),
                                 var.GetElement(2))

        # MAXIMUM ERROR
        me = self._canny.GetMaximumError()
        self._config.maximumError = (me.GetElement(0), me.GetElement(1),
                                     me.GetElement(2))

        # THRESHOLD
        self._config.threshold = self._canny.GetThreshold()

        # OUTSIDE VALUE
        self._config.outsideValue = self._canny.GetOutsideValue()
            
