import gen_utils
from module_base import ModuleBase
from module_mixins import NoConfigModuleMixin
import module_utils
import wx
import vtk


class imageFlip(NoConfigModuleMixin, ModuleBase):

    
    def __init__(self, module_manager):
        # initialise our base class
        ModuleBase.__init__(self, module_manager)

        

        self._imageFlip = vtk.vtkImageFlip()
        self._imageFlip.SetFilteredAxis(2)
        self._imageFlip.GetOutput().SetUpdateExtentToWholeExtent()
        
        module_utils.setupVTKObjectProgress(self, self._imageFlip,
                                           'Flipping image')

        NoConfigModuleMixin.__init__(
            self,
            {'vtkImageFlip' : self._imageFlip})

        self.sync_module_logic_with_config()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for input_idx in range(len(self.get_input_descriptions())):
            self.set_input(input_idx, None)

        # this will take care of all display thingies
        NoConfigModuleMixin.close(self)
        
        # get rid of our reference
        del self._imageFlip

    def get_input_descriptions(self):
        return ('vtkImageData',)

    def set_input(self, idx, inputStream):
        self._imageFlip.SetInput(inputStream)

    def get_output_descriptions(self):
        return (self._imageFlip.GetOutput().GetClassName(), )

    def get_output(self, idx):
        return self._imageFlip.GetOutput()

    def logic_to_config(self):
        pass
    
    def config_to_logic(self):
        pass
    
    def view_to_config(self):
        pass

    def config_to_view(self):
        pass
    
    def execute_module(self):
        self._imageFlip.Update()
        
