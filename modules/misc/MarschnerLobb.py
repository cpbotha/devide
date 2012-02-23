# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

from module_base import ModuleBase
from module_mixins import ScriptedConfigModuleMixin
import module_utils
import vtk
import math


class MarschnerLobb(ScriptedConfigModuleMixin, ModuleBase):
    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        # setup config
        self._config.resolution = 40

        # and then our scripted config
        configList = [
            ('Resolution: ', 'resolution', 'base:int', 'text',
             'x, y and z resolution of sampled volume.  '
             'According to the article, should be 40 to be '
             'at Nyquist.')]

        # now create the necessary VTK modules
        self._es = vtk.vtkImageEllipsoidSource()
        self._es.SetOutputScalarTypeToFloat()

        self._ic = vtk.vtkImageChangeInformation()
        self._ic.SetInputConnection(self._es.GetOutputPort())

        self._output = vtk.vtkImageData()

        # mixin ctor
        ScriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self})

        self.sync_module_logic_with_config()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for input_idx in range(len(self.get_input_descriptions())):
            self.set_input(input_idx, None)

        # this will take care of all display thingies
        ScriptedConfigModuleMixin.close(self)
        # and the baseclass close
        ModuleBase.close(self)
            
        # remove all bindings
        del self._es
        del self._ic
        
    def execute_module(self):
        e = self._config.resolution
        self._es.SetWholeExtent(0,e-1,0,e-1,0,e-1)
        spc = 2.0 / (e - 1)
        self._ic.SetOutputSpacing(spc, spc, spc)
        self._ic.SetOutputOrigin(-1.0, -1.0, -1.0)
        
        self._ic.Update()
        data = self._ic.GetOutput()

        fm = 6
        alpha = 0.25
        topa = 2.0 * (1.0 + alpha)

        dimx,dimy,dimz = data.GetDimensions()
        dx,dy,dz = data.GetSpacing()
        ox,oy,oz = data.GetOrigin()
        progress = 0.0
        pinc = 100.0 / dimz 
        for k in range(dimz):
            z = oz + k * dz
            for j in range(dimy):
                y = oy + j * dy
                for i in range(dimx):
                    x = ox + i * dx
                    rho_r = math.cos(2 * math.pi * fm * 
                        math.cos(math.pi * math.hypot(x,y) / 2.0))
                    rho = (1.0 - math.sin(math.pi * z / 2.0) + alpha * 
                        (1.0 + rho_r)) / topa
                    data.SetScalarComponentFromDouble(i,j,k,0,rho)

            progress += pinc
            self._module_manager.set_progress(progress, 'Sampling function.')

        self._output.ShallowCopy(data)

    def get_input_descriptions(self):
        return ()

    def set_input(self, idx, input_stream):
        raise Exception
    
    def get_output_descriptions(self):
        return ('Marschner-Lobb volume',)
    
    def get_output(self, idx):
        return self._output

    def config_to_logic(self):
        pass

    def logic_to_config(self):
        pass
    

        
