# geodesicActiveContour.py
# $Id: geodesicActiveContour.py,v 1.1 2004/02/27 17:02:22 cpbotha Exp $

#import fixitk as itk
from moduleBase import moduleBase
import moduleUtils
from moduleMixins import scriptedConfigModuleMixin
#import vtk
#import ConnectVTKITKPython as CVIPy

class geodesicActiveContour(scriptedConfigModuleMixin, moduleBase):

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
             'The initial distance.. [TBD]'),
            ('Sigma:', 'sigma', 'base:float', 'text',
             'Sigma.. [TBD'),
            ('Sigmoid Alpha:', 'sigmoidAlpha', 'base:float', 'text',
             'Alpha parameter for the sigmoid filter'),
            ('Sigmoid Beta:', 'sigmoidBeta', 'base:float', 'text',
             'Beta parameter for the sigmoid filter'),
            ('Propagation scaling:', 'propagationScaling', 'base:float',
             'text', 'Propagation scaling')]
        
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


        
