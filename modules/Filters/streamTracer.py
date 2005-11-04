from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtk

INTEG_TYPE = ['RK2', 'RK4', 'RK45']
INTEG_TYPE_TEXTS = ['Runge-Kutta 2', 'Runge-Kutta 4', 'Runge-Kutta 45']

class streamTracer(scriptedConfigModuleMixin, moduleBase):
    """Visualise a vector field with stream lines.

    $Revision: 1.2 $
    """

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        # 0 = RK2
        # 1 = RK4
        # 2 = RK45
        self._config.integrator = INTEG_TYPE.index('RK2')

        configList = [
            ('Integrator type:', 'integrator', 'base:int', 'choice',
             'Select an integrator for the streamlines.',
             INTEG_TYPE_TEXTS)]

        scriptedConfigModuleMixin.__init__(self, configList)

        self._streamTracer = vtk.vtkStreamTracer()
        moduleUtils.setupVTKObjectProgress(self, self._streamTracer,
                                           'Tracing stream lines.')

        self._createWindow(
            {'Module (self)' : self,
             'vtkStreamTracer' : self._streamTracer})

        self.configToLogic()
        self.logicToConfig()
        self.configToView()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)
        
        # get rid of our reference
        del self._streamTracer

    def executeModule(self):
        self._streamTracer.Update()

    def getInputDescriptions(self):
        return ('VTK Vector dataset', 'VTK source geometry')

    def setInput(self, idx, inputStream):
        if idx == 0:
            self._streamTracer.SetInput(inputStream)
            
        else:
            self._streamTracer.SetSource(inputStream)

    def getOutputDescriptions(self):
        return ('Streamlines polydata',)

    def getOutput(self, idx):
        return self._streamTracer.GetOutput()

    def logicToConfig(self):
        self._config.integrator = self._streamTracer.GetIntegratorType()
    
    def configToLogic(self):
        self._streamTracer.SetIntegratorType(self._config.integrator)

        

        
