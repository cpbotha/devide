from module_base import ModuleBase
from module_mixins import ScriptedConfigModuleMixin
import module_utils
import vtk
import wx

class myImageClip(ScriptedConfigModuleMixin, ModuleBase):
    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        self._clipper = vtk.vtkImageClip()

        module_utils.setupVTKObjectProgress(self, self._clipper,
                                           'Reading PNG images.')

        self._config.outputWholeExtent = (0,-1,0,-1,0,-1)

        configList = [
            ('OutputWholeExtent:', 'outputWholeExtent', 'tuple:float,6', 'text',
             'The size of the clip volume.')]

        ScriptedConfigModuleMixin.__init__(self, configList)

        self._viewFrame = self._createViewFrame(
            {'Module (self)' : self,
             'vtkImageClip' : self._clipper})

        self.config_to_logic()
        self.syncViewWithLogic()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for input_idx in range(len(self.get_input_descriptions())):
            self.set_input(input_idx, None)

        # this will take care of all display thingies
        ScriptedConfigModuleMixin.close(self)
        ModuleBase.close(self)
        
        # get rid of our reference
        del self._clipper

    def get_input_descriptions(self):
        return ('vtkImageData',)

    def set_input(self, idx, inputStream):
        if idx == 0:
            self._clipper.SetInput(inputStream)
        else:
            raise Exception

    def get_output_descriptions(self):
        return ('vtkImageData',)

    def get_output(self, idx):
        return self._clipper.GetOutput()

    def logic_to_config(self):
        self._config.outputWholeExtent = self._clipper.GetOutputWholeExtent()

    def config_to_logic(self):
        self._clipper.SetOutputWholeExtent( self._config.outputWholeExtent, None )

    def execute_module(self):
        self._clipper.Update()
        