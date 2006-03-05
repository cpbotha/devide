# $Id$

import itk
import module_kits.itk_kit as itk_kit
from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin

class gaussianConvolve(scriptedConfigModuleMixin, moduleBase):
    """Convolves input with Gaussian, or its first or second derivative.
    Only a single dimension is convolved (i.e. the filter is separated).
    Select which dimension in the View/Config window.

    The convolution is implemented as an IIR filter.

    $Revision: 1.4 $
    """

    _orders = ['Zero', 'First', 'Second']
    
    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        self._config.direction = 0
        self._config.sigma = 1.0
        self._config.order = 'Zero'
        self._config.normaliseAcrossScale = False        
        
        configList = [
            ('Direction:', 'direction', 'base:int', 'choice',
             'Direction in which the filter has to be applied.',
             ['0', '1', '2']),
            ('Sigma:', 'sigma', 'base:float', 'text',
             'Sigma of Gaussian kernel in world coordinates.'),

            ('Order of Gaussian', 'order', 'base:str', 'choice',
             'Convolve with Gaussian, or first or second derivative.',
             tuple(self._orders)),
            ('Normalise across scale', 'normaliseAcrossScale', 'base:bool',
             'checkbox', 'Determine and use normalisation factor.')]
        
        scriptedConfigModuleMixin.__init__(self, configList)


        # setup the pipeline
        self._gaussian = itk.itkRecursiveGaussianImageFilterF3F3_New()
        
        itk_kit.utils.setupITKObjectProgress(
            self, self._gaussian, 'itkRecursiveGaussianImageFilter',
            'Convolving with Gaussian')

        self._createWindow(
            {'Module (self)' : self,
             'itkRecursiveGaussianImageFilter' : self._gaussian})

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
        del self._gaussian

    def executeModule(self):
        self._gaussian.Update()

    def getInputDescriptions(self):
        return ('ITK Image (3D, float)',)

    def setInput(self, idx, inputStream):
        self._gaussian.SetInput(inputStream)

    def getOutputDescriptions(self):
        return ('Blurred ITK Image (3D, float)',)

    def getOutput(self, idx):
        return self._gaussian.GetOutput()

    def configToLogic(self):
        self._gaussian.SetDirection(self._config.direction)
        
        # SIGMA
        self._gaussian.SetSigma(self._config.sigma)

        # ORDER
        if self._config.order == 'Zero':
            self._gaussian.SetZeroOrder()
        elif self._config.order == 'First':
            self._gaussian.SetFirstOrder()
        elif self._config.order == 'Second':
            self._gaussian.SetSecondOrder()
        else:
            self._config.order = 'Zero'
            self._gaussian.SetZeroOrder()
        
        # NORMALISEACROSSSCALE
        self._gaussian.SetNormalizeAcrossScale(
            self._config.normaliseAcrossScale)
        

    def logicToConfig(self):
        self._config.direction = self._gaussian.GetDirection()
        
        # SIGMA
        self._config.sigma = self._gaussian.GetSigma()

        # ORDER
        # FIMXE: dammit, we can't get the order.

        # NORMALISEACROSSSCALE
        self._config.normaliseAcrossScale = self._gaussian.\
                                            GetNormalizeAcrossScale()
