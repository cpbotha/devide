import gen_utils
from module_base import ModuleBase
from module_mixins import NoConfigModuleMixin
import module_utils
import vtk

class clipPolyData(NoConfigModuleMixin, ModuleBase):
    """Given an input polydata and an implicitFunction, this will clip
    the polydata.

    All points that are inside the implicit function are kept, everything
    else is discarded.  'Inside' is defined as all points in the polydata
    where the implicit function value is greater than 0.
    """
    
    def __init__(self, module_manager):
        # initialise our base class
        ModuleBase.__init__(self, module_manager)


        self._clipPolyData = vtk.vtkClipPolyData()
        module_utils.setup_vtk_object_progress(self, self._clipPolyData,
                                           'Calculating normals')

        NoConfigModuleMixin.__init__(
            self,
            {'vtkClipPolyData' : self._clipPolyData})

        self.sync_module_logic_with_config()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for input_idx in range(len(self.get_input_descriptions())):
            self.set_input(input_idx, None)

        # this will take care of all display thingies
        NoConfigModuleMixin.close(self)
        
        # get rid of our reference
        del self._clipPolyData

    def get_input_descriptions(self):
        return ('PolyData', 'Implicit Function')

    def set_input(self, idx, inputStream):
        if idx == 0:
            self._clipPolyData.SetInput(inputStream)
        else:
            self._clipPolyData.SetClipFunction(inputStream)
            

    def get_output_descriptions(self):
        return (self._clipPolyData.GetOutput().GetClassName(), )

    def get_output(self, idx):
        return self._clipPolyData.GetOutput()

    def logic_to_config(self):
        pass
    
    def config_to_logic(self):
        pass
    
    def view_to_config(self):
        pass

    def config_to_view(self):
        pass
    
    def execute_module(self):
        self._clipPolyData.Update()
        
