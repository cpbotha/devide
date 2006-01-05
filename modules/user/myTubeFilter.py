import genUtils
from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import wx
import vtk

class myTubeFilter(scriptedConfigModuleMixin, moduleBase):

    """Simple demonstration of scriptedConfigModuleMixin-based
    wrapping of a single VTK object.

    It would of course be even easier using simpleVTKClassModuleBase.
    
    $Revision: 1.1 $
    """
    
    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)

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
        self.configToLogic()
        # and all the way up from logic -> config -> view to make sure
        self.syncViewWithLogic()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)

        moduleBase.close(self)
        
        # get rid of our reference
        del self._tubeFilter

    def getInputDescriptions(self):
        return ('vtkPolyData lines',)

    def setInput(self, idx, inputStream):
        self._tubeFilter.SetInput(inputStream)

    def getOutputDescriptions(self):
        return ('vtkPolyData tubes', )

    def getOutput(self, idx):
        return self._tubeFilter.GetOutput()

    def logicToConfig(self):
        self._config.NumberOfSides = self._tubeFilter.GetNumberOfSides()
        self._config.Radius = self._tubeFilter.GetRadius()
    
    def configToLogic(self):
        self._tubeFilter.SetNumberOfSides(self._config.NumberOfSides)
        self._tubeFilter.SetRadius(self._config.Radius)
    
    def executeModule(self):
        self._tubeFilter.GetOutput().Update()


