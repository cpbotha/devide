# geodesicActiveContour.py
# $Id: geodesicActiveContour.py,v 1.2 2004/02/27 17:19:35 cpbotha Exp $

#import fixitk as itk
from moduleBase import moduleBase
import moduleUtils
from moduleMixins import scriptedConfigModuleMixin
#import vtk
#import ConnectVTKITKPython as CVIPy

class geodesicActiveContour(scriptedConfigModuleMixin, moduleBase):

    """Module for performing Geodesic Active Contour-based segmentation on
    3D data.

    We make use of the following pipelines:<br>
    1. reader -> smoothing -> gradientMagnitude -> sigmoid -> FI<br>
    2. fastMarching -> geodesicActiveContour(FI) -> thresholder -> writer<br>
    The output of pipeline 1 is a feature image that is used by the
    geodesicActiveContour object.  Also see figure 9.18 in the ITK
    Software Guide.
    """

    def __init__(self, moduleManager):

        moduleBase.__init__(self, moduleManager)
        
        # setup defaults
        self._config.initialDistance = 5.0
        self._config.sigma = 1.0
        self._config.sigmoidAlpha = -0.5
        self._config.sigmoidBeta = 3.0
        self._config.propagationScaling = 2.0
        
        configList = [
            ('Initial Distance:', 'initialDistance', 'base:float', 'text',
             'The initial distance of the initial front.'),
            ('Sigma:', 'sigma', 'base:float', 'text',
             'Sigma parameter of the Gaussian that will be used to calculate '
             'the gradient.'),
            ('Sigmoid Alpha:', 'sigmoidAlpha', 'base:float', 'text',
             'Alpha parameter for the sigmoid filter'),
            ('Sigmoid Beta:', 'sigmoidBeta', 'base:float', 'text',
             'Beta parameter for the sigmoid filter'),
            ('Propagation scaling:', 'propagationScaling', 'base:float',
             'text', 'Propagation scaling parameter for the geodesic active '
             'contour, '
             'i.e. balloon force.  Positive for outwards, negative for '
             'inwards.')]
        
        scriptedConfigModuleMixin.__init__(self, configList)

        # temporary
        #import moduleMixins
        #reload(moduleMixins)
        
        self._createWindow({'Module (self)' : self})

        self.configToLogic()
        self.syncViewWithLogic()

    def close(self):
        scriptedConfigModuleMixin.close(self)
        moduleBase.close(self)

    def getInputDescriptions(self):
        return ('Image Data', )

    def setInput(self, idx, inputStream):
        pass

    def getOutputDescriptions(self):
        return ('Image Data', )

    def getOutput(self, idx):
        pass

    def configToLogic(self):
        pass

    def logicToConfig(self):
        pass


        
