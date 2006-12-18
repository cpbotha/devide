from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import moduleUtils
import vtk

class transformVolumeData(noConfigModuleMixin, moduleBase):
    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)
        # initialise any mixins we might have
        noConfigModuleMixin.__init__(self)


        self._imageReslice = vtk.vtkImageReslice()
        self._imageReslice.SetInterpolationModeToCubic()

        moduleUtils.setupVTKObjectProgress(self, self._imageReslice,
                                           'Resampling volume')

        self._viewFrame = self._createViewFrame(
            {'Module (self)' : self,
             'vtkImageReslice' : self._imageReslice})

        # pass the data down to the underlying logic
        self.config_to_logic()
        # and all the way up from logic -> config -> view to make sure
        self.logic_to_config()
        self.config_to_view()     

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)
        # don't forget to call the close() method of the vtkPipeline mixin
        noConfigModuleMixin.close(self)
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

    
    
        
        
        
