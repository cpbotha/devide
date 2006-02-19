# $Id$

from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtk
from module_kits.vtk_kit.mixins import VTKErrorFuncMixin

class implicitToVolume(scriptedConfigModuleMixin, moduleBase,
                       VTKErrorFuncMixin):
    """Given an implicit function, this module will evaluate it over a volume
    and yield that volume as output.

    $Revision: 1.2 $
    """

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        # setup config
        self._config.sampleDimensions = (64, 64, 64)
        self._config.modelBounds = (-1, 1, -1, 1, -1, 1)
        self._config.computeNormals = True

        # and then our scripted config
        configList = [
            ('Sample dimensions: ', 'sampleDimensions', 'tuple:float,3',
             'text', 'The dimensions of the output volume.'),
            ('Model bounds: ', 'modelBounds', 'tuple:float,6', 'text',
             'Region in world space over which the sampling is performed.'),
            ('Compute normals: ', 'computeNormals', 'base:bool', 'checkbox',
             'Must normals also be calculated and stored.')]

        # mixin ctor
        scriptedConfigModuleMixin.__init__(self, configList)
        
        # now create the necessary VTK modules
        self._sampleFunction = vtk.vtkSampleFunction()
        # setup progress for the processObject
        moduleUtils.setupVTKObjectProgress(self, self._sampleFunction,
                                           "Sampling implicit function.")
        self.add_vtk_error_handler(self._sampleFunction)

        self._createWindow(
            {'Module (self)' : self,
             'vtkSampleFunction' : self._sampleFunction})

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
        del self._sampleFunction
        
    def executeModule(self):
        self._sampleFunction.Update()
        self.check_vtk_error()

    def getInputDescriptions(self):
        return ('Implicit Function',)

    def setInput(self, idx, inputStream):
        self._sampleFunction.SetImplicitFunction(inputStream)
    
    def getOutputDescriptions(self):
	return ('VTK Image Data (volume)',)

    
    def getOutput(self, idx):
        return self._sampleFunction.GetOutput()

    def configToLogic(self):
        self._sampleFunction.SetSampleDimensions(self._config.sampleDimensions)
        self._sampleFunction.SetModelBounds(self._config.modelBounds)
        self._sampleFunction.SetComputeNormals(self._config.computeNormals)

    def logicToConfig(self):
        s = self._sampleFunction
        self._config.sampleDimensions = s.GetSampleDimensions()
        self._config.modelBounds = s.GetModelBounds()
        self._config.computeNormals = s.GetComputeNormals()
