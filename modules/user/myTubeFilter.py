import genUtils
from module_base import ModuleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import wx
import vtk

class myTubeFilter(scriptedConfigModuleMixin, ModuleBase):

    """Simple demonstration of scriptedConfigModuleMixin-based
    wrapping of a single VTK object.

    It would of course be even easier using simpleVTKClassModuleBase.
    
    $Revision: 1.1 $
    """
    
    def __init__(self, module_manager):
        # initialise our base class
        ModuleBase.__init__(self, module_manager)

        self._tubeFilter = vtk.vtkTubeFilter()
        
        moduleUtils.setupVTKObjectProgress(self, self._tubeFilter,
                                           'Generating tubes.')
                                           
        self._config.NumberOfSides = 3
        self._config.Radius = 0.01

        configList = [
            ('Number of sides:', 'NumberOfSides', 'base:int', 'text',
             'Number of sides that the tube should have.'),
            ('Tube radius:', 'Radius', 'base:float', 'text',
             'Radius of the generated tube.')]
        scriptedConfigModuleMixin.__init__(self, configList)        
        
        self._viewFrame = self._createWindow(
            {'Module (self)' : self,
             'vtkTubeFilter' : self._tubeFilter})

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
        scriptedConfigModuleMixin.close(self)

        ModuleBase.close(self)
        
        # get rid of our reference
        del self._tubeFilter

    def get_input_descriptions(self):
        return ('vtkPolyData lines',)

    def set_input(self, idx, inputStream):
        self._tubeFilter.SetInput(inputStream)

    def get_output_descriptions(self):
        return ('vtkPolyData tubes', )

    def get_output(self, idx):
        return self._tubeFilter.GetOutput()

    def logic_to_config(self):
        self._config.NumberOfSides = self._tubeFilter.GetNumberOfSides()
        self._config.Radius = self._tubeFilter.GetRadius()
    
    def config_to_logic(self):
        self._tubeFilter.SetNumberOfSides(self._config.NumberOfSides)
        self._tubeFilter.SetRadius(self._config.Radius)
    
    def execute_module(self):
        self._tubeFilter.GetOutput().Update()


