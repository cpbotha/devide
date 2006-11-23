import genUtils
from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtk
import vtktud

class MySource4D(scriptedConfigModuleMixin, moduleBase):

    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)


        self._source4d = vtktud.vtkMySource4D()
        
        moduleUtils.setupVTKObjectProgress(self, self._source4d,
                                           'Making 4D source')
        
        scriptedConfigModuleMixin.__init__(self, configList)        
        

        self._viewFrame = self._createWindow(
            {'Module (self)' : self,
             'vtkMySource4D' : self._source4d})

        # pass the data down to the underlying logic
        self.configToLogic()
        # and all the way up from logic -> config -> view to make sure
        self.logicToConfig()
        self.configToView()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)

        moduleBase.close(self)
        
        # get rid of our reference
        del self._source4d

    def getInputDescriptions(self):
        return ('None')

    def setInput(self, idx, inputStream):
        self._source4d.SetInput(inputStream)

    def getOutputDescriptions(self):
        return ('(vtkPolyData)', )

    def getOutput(self, idx):
        return self._source4d.GetOutput()

    def executeModule(self):
        self._source4d.Update()
        


