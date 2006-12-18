import genUtils
from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import moduleUtils
import wx
import vtk


class clipPolyData(moduleBase, noConfigModuleMixin):
    """Given an input polydata and an implicitFunction, this will clip
    the polydata.

    All points that are inside the implicit function are kept, everything
    else is discarded.  'Inside' is defined as all points in the polydata
    where the implicit function value is greater than 0.
    """
    
    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)
        noConfigModuleMixin.__init__(self)

        self._clipPolyData = vtk.vtkClipPolyData()
        moduleUtils.setupVTKObjectProgress(self, self._clipPolyData,
                                           'Calculating normals')
        

        self._viewFrame = self._createViewFrame(
            {'vtkClipPolyData' : self._clipPolyData})

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
        

    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()

