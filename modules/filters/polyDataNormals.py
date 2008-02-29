import genUtils
from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import moduleUtils
import vtk


class polyDataNormals(noConfigModuleMixin, moduleBase):
    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)


        self._pdNormals = vtk.vtkPolyDataNormals()
        moduleUtils.setupVTKObjectProgress(self, self._pdNormals,
                                           'Calculating normals')

        noConfigModuleMixin.__init__(
            self, {'vtkPolyDataNormals' : self._pdNormals})
        
        self.sync_module_logic_with_config()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        noConfigModuleMixin.close(self)
        
        # get rid of our reference
        del self._pdNormals

    def get_input_descriptions(self):
        return ('vtkPolyData',)

    def set_input(self, idx, inputStream):
        self._pdNormals.SetInput(inputStream)

    def get_output_descriptions(self):
        return (self._pdNormals.GetOutput().GetClassName(), )

    def get_output(self, idx):
        return self._pdNormals.GetOutput()

    def logic_to_config(self):
        pass
    
    def config_to_logic(self):
        pass
    
    def view_to_config(self):
        pass

    def config_to_view(self):
        pass
    
    def execute_module(self):
        self._pdNormals.Update()
        
    def streaming_execute_module(self):
        self._pdNormals.Update()

