# $Id: cannyEdgeDetection.py 1957 2006-03-05 22:49:30Z cpbotha $

import itk
import module_kits.itk_kit as itk_kit
from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin

class DanielssonDistance(scriptedConfigModuleMixin, moduleBase):
    """Calculates distance image of input image.

    The input image can either contain marked objects or binary objects.
    """
    
    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        self._config.squared_distance = False
        self._config.binary_input = True

        configList = [
            ('Squared distance:', 'squared_distance', 'base:bool', 'checkbox',
             'Should the distance output be squared (faster) or true.'),
            ('Binary input:', 'binary_input', 'base:bool', 'checkbox',
             'Does the input contain marked objects, or binary (yes/no) '
             'objects.')]
             
        scriptedConfigModuleMixin.__init__(self, configList)

        # setup the pipeline
        self._dist_filter = itk.itkDanielssonDistanceMapImageFilterF3F3_New()
        # THIS HAS TO BE ON.  SO THERE.
        self._dist_filter.SetUseImageSpacing(True)
        
        itk_kit.utils.setupITKObjectProgress(
            self, self._dist_filter, 'itkDanielssonDistanceMapImageFilter',
            'Calculating distance map.')

        self._createWindow(
            {'Module (self)' : self,
             'itkDanielssonDistanceMapImageFilter' : self._dist_filter})

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
        del self._dist_filter

    def executeModule(self):
        self._dist_filter.Update()

    def getInputDescriptions(self):
        return ('ITK Image (3D, float)',)

    def setInput(self, idx, inputStream):
        self._dist_filter.SetInput(inputStream)

    def getOutputDescriptions(self):
        return ('Distance map (ITK 3D, float)', 'Voronoi map (ITK 3D float)')

    def getOutput(self, idx):
        return self._dist_filter.GetOutput()

    def configToLogic(self):
        self._dist_filter.SetInputIsBinary(self._config.binary_input)
        self._dist_filter.SetSquaredDistance(self._config.squared_distance)

    def logicToConfig(self):
        self._config.binary_input = self._dist_filter.GetInputIsBinary()
        self._config.squared_distance = self._dist_filter.GetSquaredDistance()
        
