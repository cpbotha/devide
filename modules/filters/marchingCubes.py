from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtk


class marchingCubes(scriptedConfigModuleMixin, moduleBase):

    def __init__(self, moduleManager):

        # call parent constructor
        moduleBase.__init__(self, moduleManager)

        self._contourFilter = vtk.vtkMarchingCubes()

        moduleUtils.setupVTKObjectProgress(self, self._contourFilter,
                                           'Extracting iso-surface')
        

        # now setup some defaults before our sync
        self._config.iso_value = 128

        config_list = [
            ('ISO value:', 'iso_value', 'base:float', 'text',
             'Surface will pass through points with this value.')]
        scriptedConfigModuleMixin.__init__(self, config_list)

        self._viewFrame = self._createWindow(
            {'Module (self)' : self,
             'vtkMarchingCubes' : self._contourFilter})

        # pass the data down to the underlying logic
        self.configToLogic()
        # and all the way up from logic -> config -> view to make sure
        self.logicToConfig()
        self.configToView()
        
    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        self.setInput(0, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)

        moduleBase.close(self)
        
        # get rid of our reference
        del self._contourFilter

    def getInputDescriptions(self):
	return ('vtkImageData',)

    def setInput(self, idx, inputStream):
        self._contourFilter.SetInput(inputStream)

    def getOutputDescriptions(self):
	return (self._contourFilter.GetOutput().GetClassName(),)
    

    def getOutput(self, idx):
        return self._contourFilter.GetOutput()

    def logicToConfig(self):
        self._config.iso_value = self._contourFilter.GetValue(0)

    def configToLogic(self):
        self._contourFilter.SetValue(0, self._config.iso_value)

    def executeModule(self):
        self._contourFilter.Update()
        

