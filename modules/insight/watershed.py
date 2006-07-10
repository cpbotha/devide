# $Id$

import itk
import genUtils
import module_kits.itk_kit
from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin

class watershed(scriptedConfigModuleMixin, moduleBase):


    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        # pre-processing on input image: it will be thresholded
        self._config.threshold = 0.1
        # flood level: this will be the starting level of precipitation
        self._config.level = 0.1

        configList = [
            ('Threshold:', 'threshold', 'base:float', 'text',
             'Pre-processing image threshold (0.0-1.0).'),
            ('Level:', 'level', 'base:float', 'text',
             'Initial precipitation level (0.0-1.0).')]
        
        scriptedConfigModuleMixin.__init__(self, configList)


        # setup the pipeline
        if3 = itk.Image[itk.F, 3]
        self._watershed = itk.WatershedImageFilter[if3].New()
        
        module_kits.itk_kit.utils.setupITKObjectProgress(
            self, self._watershed, 'itkWatershedImageFilter',
            'Performing watershed')

        self._createWindow(
            {'Module (self)' : self,
             'itkWatershedImageFilter' : self._watershed})

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
        # and the baseclass close
        moduleBase.close(self)
            
        # remove all bindings
        del self._watershed

    def executeModule(self):
        self._watershed.Update()
        self._watershed.GetOutput().Update()
        # the watershed module is REALLY CRAP about setting progress to 100,
        # so we do it here.
        self._moduleManager.setProgress(100, "Watershed complete.")

    def getInputDescriptions(self):
        return ('ITK Image (3D, float)',)

    def setInput(self, idx, inputStream):
        self._watershed.SetInput(inputStream)

    def getOutputDescriptions(self):
        return ('ITK Image (3D, unsigned long)',)

    def getOutput(self, idx):
        return self._watershed.GetOutput()

    def configToLogic(self):
        self._config.threshold = genUtils.clampVariable(
            self._config.threshold, 0.0, 1.0)
        self._watershed.SetThreshold(self._config.threshold)
        
        self._config.level = genUtils.clampVariable(
            self._config.level, 0.0, 1.0)
        self._watershed.SetLevel(self._config.level)

    def logicToConfig(self):
        self._config.threshold = self._watershed.GetThreshold()
        self._config.level = self._watershed.GetLevel()

