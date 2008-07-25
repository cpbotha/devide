import genUtils
from module_base import ModuleBase
from module_mixins import NoConfigModuleMixin
import module_utils
import vtktud

class imageCurvatureMagnitude(ModuleBase, NoConfigModuleMixin):

    def __init__(self, module_manager):
        # initialise our base class
        ModuleBase.__init__(self, module_manager)
        NoConfigModuleMixin.__init__(self)

        self._imageCurvatureMagnitude = vtktud.vtkImageCurvatureMagnitude()
        
#        module_utils.setupVTKObjectProgress(self, self._clipPolyData,
#                                          'Calculating normals')

        self._viewFrame = self._createViewFrame(
            {'ImageCurvatureMagnitude' : self._imageCurvatureMagnitude})

        # pass the data down to the underlying logic
        self.config_to_logic()
        # and all the way up from logic -> config -> view to make sure
        self.syncViewWithLogic()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        NoConfigModuleMixin.close(self)
        
        # get rid of our reference
        del self._imageCurvatureMagnitude

    def get_input_descriptions(self):
        return ('vtkImageData', 'vtkImageData', 'vtkImageData','vtkImageData', 'vtkImageData')

    def set_input(self, idx, inputStream):
        self._imageCurvatureMagnitude.SetInput(idx, inputStream)

    def get_output_descriptions(self):
        return ('vtkImageData',)

    def get_output(self, idx):
        return self._imageCurvatureMagnitude.GetOutput()

    def logic_to_config(self):
        pass
    
    def config_to_logic(self):
        pass
    
    def view_to_config(self):
        pass

    def config_to_view(self):
        pass
    
    def execute_module(self):
        self._imageCurvatureMagnitude.Update()

    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()

