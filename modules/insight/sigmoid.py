# $Id$

import itk
import module_kits.itk_kit as itk_kit
from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin

class sigmoid(scriptedConfigModuleMixin, moduleBase):
    """Perform sigmoid transformation on all input voxels.

    f(x) = (max - min) frac{1}{1 + exp(- frac{x - beta}{alpha})} + min

    $Revision: 1.3 $
    """
    
    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        self._config.alpha = - 0.5
        self._config.beta = 3.0
        self._config.min = 0.0
        self._config.max = 1.0
        
        configList = [
            ('Alpha:', 'alpha', 'base:float', 'text',
             'Alpha parameter for the sigmoid filter'),
            ('Beta:', 'beta', 'base:float', 'text',
             'Beta parameter for the sigmoid filter'),
            ('Minimum:', 'min', 'base:float', 'text',
             'Minimum output of sigmoid transform'),
            ('Maximum:', 'max', 'base:float', 'text',
             'Maximum output of sigmoid transform')]
        
        scriptedConfigModuleMixin.__init__(self, configList)

        self._sigmoid = itk.itkSigmoidImageFilterF3F3_New()
        
        itk_kit.utils.setupITKObjectProgress(
            self, self._sigmoid,
            'itkSigmoidImageFilter',
            'Performing sigmoid transformation')

        self._createWindow(
            {'Module (self)' : self,
             'itkSigmoidImageFilter' :
             self._sigmoid})

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
        del self._sigmoid

    def executeModule(self):
        self._sigmoid.Update()

    def getInputDescriptions(self):
        return ('Input Image (ITK Image 3D, float)',)

    def setInput(self, idx, inputStream):
        self._sigmoid.SetInput(inputStream)

    def getOutputDescriptions(self):
        return ('Sigmoid Image (ITK Image, 3D, float)',)

    def getOutput(self, idx):
        return self._sigmoid.GetOutput()

    def configToLogic(self):
        self._sigmoid.SetAlpha(self._config.alpha)
        self._sigmoid.SetBeta(self._config.beta)
        self._sigmoid.SetOutputMinimum(self._config.min)
        self._sigmoid.SetOutputMaximum(self._config.max)

    def logicToConfig(self):
        # there're no getters for alpha, beta, min or max (itk 1.6)
        pass
