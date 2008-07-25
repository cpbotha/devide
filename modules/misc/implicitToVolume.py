# $Id$

from module_base import ModuleBase
from module_mixins import ScriptedConfigModuleMixin
import module_utils
import vtk

class implicitToVolume(ScriptedConfigModuleMixin, ModuleBase):

    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        # setup config
        self._config.sampleDimensions = (64, 64, 64)
        self._config.modelBounds = (-1, 1, -1, 1, -1, 1)
        # we init normals to off, they EAT memory (3 elements per point!)
        self._config.computeNormals = False

        # and then our scripted config
        configList = [
            ('Sample dimensions: ', 'sampleDimensions', 'tuple:float,3',
             'text', 'The dimensions of the output volume.'),
            ('Model bounds: ', 'modelBounds', 'tuple:float,6', 'text',
             'Region in world space over which the sampling is performed.'),
            ('Compute normals: ', 'computeNormals', 'base:bool', 'checkbox',
             'Must normals also be calculated and stored.')]

        
        # now create the necessary VTK modules
        self._sampleFunction = vtk.vtkSampleFunction()
        # this is more than good enough.
        self._sampleFunction.SetOutputScalarTypeToFloat()
        # setup progress for the processObject
        module_utils.setupVTKObjectProgress(self, self._sampleFunction,
                                           "Sampling implicit function.")
        

        self._example_input = None

        # mixin ctor
        ScriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
             'vtkSampleFunction' : self._sampleFunction})

        self.sync_module_logic_with_config()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        ScriptedConfigModuleMixin.close(self)
        # and the baseclass close
        ModuleBase.close(self)
            
        # remove all bindings
        del self._sampleFunction
        del self._example_input
        
    def execute_module(self):
        # if we have an example input volume, copy its bounds and resolution
        i1 = self._example_input
        try:
            self._sampleFunction.SetModelBounds(i1.GetBounds())
            self._sampleFunction.SetSampleDimensions(i1.GetDimensions())
            
        except AttributeError:
            # if we couldn't get example_input metadata, just use our config
            self.config_to_logic()

        self._sampleFunction.Update()
        

    def get_input_descriptions(self):
        return ('Implicit Function', 'Example vtkImageData')

    def set_input(self, idx, inputStream):
        if idx == 0:
            self._sampleFunction.SetImplicitFunction(inputStream)
        else:
            self._example_input = inputStream
    
    def get_output_descriptions(self):
	return ('VTK Image Data (volume)',)
    
    def get_output(self, idx):
        return self._sampleFunction.GetOutput()

    def config_to_logic(self):
        self._sampleFunction.SetSampleDimensions(self._config.sampleDimensions)
        self._sampleFunction.SetModelBounds(self._config.modelBounds)
        self._sampleFunction.SetComputeNormals(self._config.computeNormals)

    def logic_to_config(self):
        s = self._sampleFunction
        self._config.sampleDimensions = s.GetSampleDimensions()
        self._config.modelBounds = s.GetModelBounds()
        self._config.computeNormals = s.GetComputeNormals()
