from module_base import ModuleBase
from module_mixins import NoConfigModuleMixin
import module_utils
import vtk

class testModule2(NoConfigModuleMixin, ModuleBase):
    """Resample volume according to 4x4 homogeneous transform.
    """

    def __init__(self, module_manager):
        # initialise our base class
        ModuleBase.__init__(self, module_manager)
        # initialise any mixins we might have
        NoConfigModuleMixin.__init__(self)


        self._imageReslice = vtk.vtkImageReslice()
        self._imageReslice.SetInterpolationModeToCubic()

        self._matrixToHT = vtk.vtkMatrixToHomogeneousTransform()
        self._matrixToHT.Inverse()


        module_utils.setupVTKObjectProgress(self, self._imageReslice,
                                           'Resampling volume')

        self._viewFrame = self._createViewFrame(
            {'Module (self)' : self,
             'vtkImageReslice' : self._imageReslice})

        # pass the data down to the underlying logic
        self.config_to_logic()
        # and all the way up from logic -> config -> view to make sure
        self.syncViewWithLogic()     

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)
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
            try:
                self._matrixToHT.SetInput(inputStream.GetMatrix())
                
            except AttributeError:
                # this means the inputStream has no GetMatrix()
                # i.e. it could be None or just the wrong type
                # if it's none, we just have to disconnect
                if inputStream == None:
                    self._matrixToHT.SetInput(None)
                    self._imageReslice.SetResliceTransform(None)

                # if not, we have to complain
                else:
                    raise TypeError, \
                          "transformVolume input 2 requires a transform."
            
            else:
                self._imageReslice.SetResliceTransform(self._matrixToHT)
                    

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

    
    
        
        
        
