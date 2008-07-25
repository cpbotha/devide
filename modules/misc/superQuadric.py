# $Id$

from module_base import ModuleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtk


class superQuadric(scriptedConfigModuleMixin, ModuleBase):
    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        # setup config
        self._config.toroidal = True
        self._config.thickness = 0.3333
        self._config.phiRoundness = 0.2
        self._config.thetaRoundness = 0.8
        self._config.size = 0.5

        self._config.center = (0,0,0)
        self._config.scale = (1,1,1)

        self._config.thetaResolution = 64
        self._config.phiResolution = 64

        # and then our scripted config
        configList = [
            ('Toroidal: ', 'toroidal', 'base:bool', 'checkbox',
             'Should the quadric be toroidal.'),
            ('Thickness: ', 'thickness', 'base:float', 'text',
             'Thickness of the toroid, scaled between 0 and 1'),
            ('Phi Roundness: ', 'phiRoundness', 'base:float', 'text',
             'Controls shape of superquadric'),
            ('Theta Roundness: ', 'thetaRoundness', 'base:float', 'text',
             'Controls shape of superquadric'),
            ('Size: ', 'size', 'base:float', 'text',
             'The size of the superquadric.'),
            ('Centre: ', 'center', 'tuple:float,3', 'text',
             'The translation transform of the resultant superquadric.'),
            ('Scale: ', 'scale', 'tuple:float,3', 'text',
             'The scale transformof the resultant superquadric.'),
            ('Theta resolution: ', 'thetaResolution', 'base:int', 'text',
             'The resolution of the output polydata'),
            ('Phi resolution: ', 'phiResolution', 'base:int', 'text',
             'The resolution of the output polydata')]

        # now create the necessary VTK modules
        self._superquadric = vtk.vtkSuperquadric()
        self._superquadricSource = vtk.vtkSuperquadricSource()

        # we need these temporary outputs
        self._outputs = [self._superquadric, vtk.vtkPolyData()]
        
        # setup progress for the processObject
        moduleUtils.setupVTKObjectProgress(self, self._superquadricSource,
                                           "Synthesizing polydata.")

        # mixin ctor
        scriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
             'vtkSuperquadric' : self._superquadric,
             'vtkSuperquadricSource' : self._superquadricSource})

        self.sync_module_logic_with_config()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)
        # and the baseclass close
        ModuleBase.close(self)
            
        # remove all bindings
        del self._superquadricSource
        del self._superquadric
        
    def execute_module(self):
        # when we're executed, outputs become active
        self._superquadricSource.Update()
        

        # self._outputs[0] (the superquadric implicit) is always ready


    def get_input_descriptions(self):
        return ()

    def set_input(self, idx, input_stream):
	raise Exception
    
    def get_output_descriptions(self):
	return ('Implicit function',
                'Polydata')
    
    def get_output(self, idx):
        #return self._outputs[idx]
        
        if idx == 0:
            return self._superquadric
        else:
            return self._superquadricSource.GetOutput()


    def config_to_logic(self):
        # sanity check
        if self._config.thickness < 0.0:
            self._config.thickness = 0.0
        elif self._config.thickness > 1.0:
            self._config.thickness = 1.0
        
        for obj in (self._superquadric, self._superquadricSource):
            obj.SetToroidal(self._config.toroidal)
            obj.SetThickness(self._config.thickness)
            obj.SetPhiRoundness(self._config.phiRoundness)
            obj.SetThetaRoundness(self._config.thetaRoundness)
            obj.SetSize(self._config.size)
            obj.SetCenter(self._config.center)
            obj.SetScale(self._config.scale)

        # only applicable to the source
        self._superquadricSource.SetThetaResolution(
            self._config.thetaResolution)
        self._superquadricSource.SetPhiResolution(
            self._config.phiResolution)

    def logic_to_config(self):
        s = self._superquadric
        self._config.toroidal = s.GetToroidal()
        self._config.thickness = s.GetThickness()
        self._config.phiRoundness = s.GetPhiRoundness()
        self._config.thetaRoundness = s.GetThetaRoundness()
        self._config.size = s.GetSize()
        self._config.center = s.GetCenter()
        self._config.scale = s.GetScale()

        ss = self._superquadricSource
        self._config.thetaResolution = ss.GetThetaResolution()
        self._config.phiResolution = ss.GetPhiResolution()

    

        
