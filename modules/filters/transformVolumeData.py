from module_base import ModuleBase
from module_mixins import NoConfigModuleMixin
import module_utils
import vtk

class transformVolumeData(NoConfigModuleMixin, ModuleBase):
    def __init__(self, module_manager):
        # initialise our base class
        ModuleBase.__init__(self, module_manager)

        self._imageReslice = vtk.vtkImageReslice()
        self._imageReslice.SetInterpolationModeToCubic()

        # initialise any mixins we might have
        NoConfigModuleMixin.__init__(
            self,
            {'Module (self)' : self,
             'vtkImageReslice' : self._imageReslice})


        module_utils.setup_vtk_object_progress(self, self._imageReslice,
                                           'Resampling volume')

        self.sync_module_logic_with_config()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for input_idx in range(len(self.get_input_descriptions())):
            self.set_input(input_idx, None)
        # don't forget to call the close() method of the vtkPipeline mixin
        NoConfigModuleMixin.close(self)
        # get rid of our reference
        del self._imageReslice

    def get_input_descriptions(self):
	return ('VTK Image Data', 'VTK Transform')

    def set_input(self, idx, inputStream):
        if idx == 0:
            self._imageReslice.SetInput(inputStream)
        else:
            if inputStream == None:
                # disconnect
                self._imageReslice.SetResliceTransform(None)

            else:
                # resliceTransform transforms the resampling grid, which
                # is equivalent to transforming the volume with its inverse
                self._imageReslice.SetResliceTransform(
                    inputStream.GetInverse())

    def get_output_descriptions(self):
        return ('Transformed VTK Image Data',)

    def get_output(self, idx):
        return self._imageReslice.GetOutput()

    def logic_to_config(self):
        pass

    def config_to_logic(self):
        pass
    

    def view_to_config(self):
        pass

    def config_to_view(self):
        pass
    
    def execute_module(self):
        self._imageReslice.Update()
