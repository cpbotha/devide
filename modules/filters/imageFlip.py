import genUtils
from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import moduleUtils
import wx
import vtk


class imageFlip(moduleBase, noConfigModuleMixin):

    
    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)
        noConfigModuleMixin.__init__(self)

        self._imageFlip = vtk.vtkImageFlip()
        self._imageFlip.SetFilteredAxis(2)
        self._imageFlip.GetOutput().SetUpdateExtentToWholeExtent()
        
        moduleUtils.setupVTKObjectProgress(self, self._imageFlip,
                                           'Flipping image')
        

        self._viewFrame = self._createViewFrame(
            {'vtkImageFlip' : self._imageFlip})

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

        # this will take care of all display thingies
        noConfigModuleMixin.close(self)
        
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
        

    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        self._viewFrame.Show(True)
        self._viewFrame.Raise()


