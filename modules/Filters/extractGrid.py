from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtk
import vtkdevide

class extractGrid(scriptedConfigModuleMixin, moduleBase):
    """Subsamples input dataset.

    This module makes use of the ParaView vtkPVExtractVOI class, which can
    handle structured points, structured grids and rectilinear grids.

    $Revision: 1.3 $
    """

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        self._config.sampleRate = (1, 1, 1)

        configList = [
            ('Sample rate:', 'sampleRate', 'tuple:int,3', 'tupleText',
             'Subsampling rate.')]

        scriptedConfigModuleMixin.__init__(self, configList)

        self._extractGrid = vtkdevide.vtkPVExtractVOI()
        
        moduleUtils.setupVTKObjectProgress(self, self._extractGrid,
                                           'Subsampling structured grid.')

        self._createWindow(
            {'Module (self)' : self,
             'vtkExtractGrid' : self._extractGrid})

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
        
        # get rid of our reference
        del self._extractGrid

    def executeModule(self):
        self._extractGrid.Update()

    def getInputDescriptions(self):
        return ('VTK Dataset',)

    def setInput(self, idx, inputStream):
        self._extractGrid.SetInput(inputStream)

    def getOutputDescriptions(self):
        return ('Subsampled VTK Dataset',)

    def getOutput(self, idx):
        return self._extractGrid.GetOutput()

    def logicToConfig(self):
        self._config.sampleRate = self._extractGrid.GetSampleRate()
    
    def configToLogic(self):
        self._extractGrid.SetSampleRate(self._config.sampleRate)
        
