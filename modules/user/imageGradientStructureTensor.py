import gen_utils
from module_base import ModuleBase
from module_mixins import NoConfigModuleMixin
import module_utils
import vtktud

class imageGradientStructureTensor(ModuleBase, NoConfigModuleMixin):

    def __init__(self, module_manager):
        # initialise our base class
        ModuleBase.__init__(self, module_manager)
        NoConfigModuleMixin.__init__(self)

        self._imageGradientStructureTensor = vtktud.vtkImageGradientStructureTensor()
        
#        module_utils.setup_vtk_object_progress(self, self._clipPolyData,
#                                          'Calculating normals')

        self._viewFrame = self._createViewFrame(
            {'ImageGradientStructureTensor' : self._imageGradientStructureTensor})

        # pass the data down to the underlying logic
        self.config_to_logic()
        # and all the way up from logic -> config -> view to make sure
        self.syncViewWithLogic()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for input_idx in range(len(self.get_input_descriptions())):
            self.set_input(input_idx, None)

        # this will take care of all display thingies
        NoConfigModuleMixin.close(self)
        
        # get rid of our reference
        del self._imageGradientStructureTensor

    def get_input_descriptions(self):
        return ('vtkImageData', 'vtkImageData', 'vtkImageData')

    def set_input(self, idx, inputStream):
        self._imageGradientStructureTensor.SetInput(idx, inputStream)

    def get_output_descriptions(self):
        return ('vtkImageData',)

    def get_output(self, idx):
        return self._imageGradientStructureTensor.GetOutput()

    def logic_to_config(self):
        pass
    
    def config_to_logic(self):
        pass
    
    def view_to_config(self):
        pass

    def config_to_view(self):
        pass
    
    def execute_module(self):
        self._imageGradientStructureTensor.Update()

    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()

