# $Id: cannyEdgeDetection.py 1957 2006-03-05 22:49:30Z cpbotha $

import itk
import module_kits.itk_kit as itk_kit
from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin

class DanielssonDistance(scriptedConfigModuleMixin, moduleBase):
    
    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        self._config.squared_distance = False
        self._config.binary_input = True
        self._config.image_spacing = True

        configList = [
            ('Squared distance:', 'squared_distance', 'base:bool', 'checkbox',
             'Should the distance output be squared (faster) or true.'),
            ('Use image spacing:', 'image_spacing', 'base:bool',
             'checkbox', 'Use image spacing in distance calculation.'),
            ('Binary input:', 'binary_input', 'base:bool', 'checkbox',
             'Does the input contain marked objects, or binary (yes/no) '
             'objects.')]
             
        scriptedConfigModuleMixin.__init__(self, configList)

        # setup the pipeline
        imageF3 = itk.Image[itk.F, 3]
        self._dist_filter = itk.DanielssonDistanceMapImageFilter[
            imageF3, imageF3].New()
        
        # THIS HAS TO BE ON.  SO THERE.
        #self._dist_filter.SetUseImageSpacing(True)
        
        itk_kit.utils.setupITKObjectProgress(
            self, self._dist_filter, 'DanielssonDistanceMapImageFilter',
            'Calculating distance map.')

        self._createWindow(
            {'Module (self)' : self,
             'itkDanielssonDistanceMapImageFilter' : self._dist_filter})

        self.config_to_logic()
        self.logic_to_config()
        self.config_to_view()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)
        # and the baseclass close
        moduleBase.close(self)
            
        # remove all bindings
        del self._dist_filter

    def execute_module(self):
        self._dist_filter.Update()

    def get_input_descriptions(self):
        return ('ITK Image (3D, float)',)

    def set_input(self, idx, inputStream):
        self._dist_filter.SetInput(inputStream)

    def get_output_descriptions(self):
        return ('Distance map (ITK 3D, float)', 'Voronoi map (ITK 3D float)')

    def get_output(self, idx):
        return self._dist_filter.GetOutput()

    def config_to_logic(self):
        self._dist_filter.SetInputIsBinary(self._config.binary_input)
        self._dist_filter.SetSquaredDistance(self._config.squared_distance)
        self._dist_filter.SetUseImageSpacing(self._config.image_spacing)

    def logic_to_config(self):
        self._config.binary_input = self._dist_filter.GetInputIsBinary()
        self._config.squared_distance = self._dist_filter.GetSquaredDistance()
        self._config._image_spacing = self._dist_filter.GetUseImageSpacing()
        
