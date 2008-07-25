# $Id$

from module_base import ModuleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtktud

class gaussianKernel(scriptedConfigModuleMixin, ModuleBase):
    """First test of a gaussian implicit kernel
    
    $Revision: 1.1 $
    """

    def __init__(self, moduleManager):
        ModuleBase.__init__(self, moduleManager)

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

        self.config_to_logic()
        self.syncViewWithLogic()

    def close(self):
        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)

        # and the baseclass close
        ModuleBase.close(self)
            
        # remove all bindings
        del self._gaussianKernel
        
    def execute_module(self):
        return ()
    
    def get_input_descriptions(self):
        return ()

    def set_input(self, idx, input_stream):
        raise Exception
    
    def get_output_descriptions(self):
        return ('vtkSeparableKernel',)
    
    def get_output(self, idx):
        return self._gaussianKernel

    def config_to_logic(self):
        # sanity check
        if self._config.standardDeviation < 0.0:
            self._config.standardDeviation = 0.0
        if self._config.support < 0.0:
            self._config.support = 0.0
        
        self._gaussianKernel.SetOrder( self._config.order )
        self._gaussianKernel.SetStandardDeviation( self._config.standardDeviation )
        self._gaussianKernel.SetSupport( self._config.support )
        
    def logic_to_config(self):
        self._config.order = self._gaussianKernel.GetOrder()
        self._config.standardDeviation = self._gaussianKernel.GetStandardDeviation()
        self._config.support = self._gaussianKernel.GetSupport()
