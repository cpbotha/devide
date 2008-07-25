# $Id$

from module_base import ModuleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtktud

class cubicBCSplineKernel(scriptedConfigModuleMixin, ModuleBase):
    """First test of a cubic B-Spline implicit kernel
    
    $Revision: 1.1 $
    """

    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        # setup config
        self._config.order = 0
        self._config.support = 4.0
        self._config.B = 0.0;
        self._config.C = 0.5;

        # and then our scripted config
        configList = [
            ('Order: ', 'order', 'base:int', 'text',
             'The order of the cubic B-Spline kernel (0-2).'),
            ('B: ', 'B', 'base:float', 'text',
             'B'),
            ('C: ', 'C', 'base:float', 'text',
             'C'),
            ('Support: ', 'support', 'base:float', 'text',
             'The support of the cubic B-Spline kernel.')]

        # mixin ctor
        scriptedConfigModuleMixin.__init__(self, configList)
        
        # now create the necessary VTK modules
        self._cubicBCSplineKernel = vtktud.vtkCubicBCSplineKernel()

        # setup progress for the processObject
#        moduleUtils.setupVTKObjectProgress(self, self._superquadricSource,
#                                           "Synthesizing polydata.")

        self._createWindow(
            {'Module (self)' : self,
             'vtkCubicBCSplineKernel' : self._cubicBCSplineKernel})

        self.config_to_logic()
        self.syncViewWithLogic()

    def close(self):
        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)

        # and the baseclass close
        ModuleBase.close(self)
            
        # remove all bindings
        del self._cubicBCSplineKernel
        
    def execute_module(self):
        return ()
    
    def get_input_descriptions(self):
        return ()

    def set_input(self, idx, input_stream):
        raise Exception
    
    def get_output_descriptions(self):
        return ('vtkSeparableKernel',)
    
    def get_output(self, idx):
        return self._cubicBCSplineKernel

    def config_to_logic(self):
        # sanity check
        if self._config.support < 0.0:
            self._config.support = 0.0
        
        self._cubicBCSplineKernel.SetOrder( self._config.order )
        self._cubicBCSplineKernel.SetB( self._config.B )
        self._cubicBCSplineKernel.SetC( self._config.C )
        self._cubicBCSplineKernel.SetSupport( self._config.support )
        
    def logic_to_config(self):
        self._config.order = self._cubicBCSplineKernel.GetOrder()
        self._config.B = self._cubicBCSplineKernel.GetB()
        self._config.C = self._cubicBCSplineKernel.GetC()
        self._config.support = self._cubicBCSplineKernel.GetSupport()
