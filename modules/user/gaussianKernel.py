# $Id: gaussianKernel.py,v 1.1 2006/01/05 14:58:32 cpbotha Exp $

from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtktud

class gaussianKernel(scriptedConfigModuleMixin, moduleBase):
    """First test of a gaussian implicit kernel
    
    $Revision: 1.1 $
    """

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        # setup config
        self._config.order = 0
        self._config.standardDeviation = 1.0
        self._config.support = 3.0 * self._config.standardDeviation

        # and then our scripted config
        configList = [
            ('Order: ', 'order', 'base:int', 'text',
             'The order of the gaussian kernel (0-2).'),
            ('Standard deviation: ', 'standardDeviation', 'base:float', 'text',
             'The standard deviation (width) of the gaussian kernel.'),
            ('Support: ', 'support', 'base:float', 'text',
             'The support of the gaussian kernel.')]

        # mixin ctor
        scriptedConfigModuleMixin.__init__(self, configList)
        
        # now create the necessary VTK modules
        self._gaussianKernel = vtktud.vtkGaussianKernel()

        # setup progress for the processObject
#        moduleUtils.setupVTKObjectProgress(self, self._superquadricSource,
#                                           "Synthesizing polydata.")

        self._createWindow(
            {'Module (self)' : self,
             'vtkGaussianKernel' : self._gaussianKernel})

        self.configToLogic()
        self.syncViewWithLogic()

    def close(self):
        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)

        # and the baseclass close
        moduleBase.close(self)
            
        # remove all bindings
        del self._gaussianKernel
        
    def executeModule(self):
        return ()
    
    def getInputDescriptions(self):
        return ()

    def setInput(self, idx, input_stream):
        raise Exception
    
    def getOutputDescriptions(self):
        return ('vtkSeparableKernel',)
    
    def getOutput(self, idx):
        return self._gaussianKernel

    def configToLogic(self):
        # sanity check
        if self._config.standardDeviation < 0.0:
            self._config.standardDeviation = 0.0
        if self._config.support < 0.0:
            self._config.support = 0.0
        
        self._gaussianKernel.SetOrder( self._config.order )
        self._gaussianKernel.SetStandardDeviation( self._config.standardDeviation )
        self._gaussianKernel.SetSupport( self._config.support )
        
    def logicToConfig(self):
        self._config.order = self._gaussianKernel.GetOrder()
        self._config.standardDeviation = self._gaussianKernel.GetStandardDeviation()
        self._config.support = self._gaussianKernel.GetSupport()
