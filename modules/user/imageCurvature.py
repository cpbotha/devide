import genUtils
from module_base import ModuleBase
from moduleMixins import noConfigModuleMixin
import moduleUtils
import vtktud

class imageCurvature(ModuleBase, noConfigModuleMixin):
    """Calculates image curvature with VTKTUD vtkImageCurvature filter.
    
    You need 8 inputs, and in the following sequence: dx, dy, dz,
    dxx, dyy, dzz, dxy, dxz, dyz.
    
    This will output some curvature measure.  The underlying filter will
    be adapted to make the raw curvature data (principal curvatures 
    and directions of the isophote surface) available as well.
    
    All code by Joris van Zwieten.  This bit of documentation by cpbotha.
    """

    def __init__(self, module_manager):
        # initialise our base class
        ModuleBase.__init__(self, module_manager)
        noConfigModuleMixin.__init__(self)

        self._imageCurvature = vtktud.vtkImageCurvature()
        
#        moduleUtils.setupVTKObjectProgress(self, self._clipPolyData,
#                                          'Calculating normals')

        self._viewFrame = self._createViewFrame(
            {'ImageCurvature' : self._imageCurvature})

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
        noConfigModuleMixin.close(self)
        
        # get rid of our reference
        del self._imageCurvature

    def get_input_descriptions(self):
        return ('dx', 'dy', 'dz', 'dxx', 'dyy', 'dzz', 'dxy', 'dxz', 'dyz')

    def set_input(self, idx, inputStream):
        self._imageCurvature.SetInput(idx, inputStream)

    def get_output_descriptions(self):
        return ('vtkImageData',)

    def get_output(self, idx):
        return self._imageCurvature.GetOutput()

    def logic_to_config(self):
        pass
    
    def config_to_logic(self):
        pass
    
    def view_to_config(self):
        pass

    def config_to_view(self):
        pass
    
    def execute_module(self):
        self._imageCurvature.Update()

    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()

