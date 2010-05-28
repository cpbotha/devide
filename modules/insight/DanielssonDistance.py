# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

import itk
import module_kits.itk_kit as itk_kit
from module_base import ModuleBase
from module_mixins import ScriptedConfigModuleMixin

class DanielssonDistance(ScriptedConfigModuleMixin, ModuleBase):
    
    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

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
             
        # setup the pipeline
        imageF3 = itk.Image[itk.F, 3]
        self._dist_filter = None
        self._create_pipeline(imageF3)
        
        # THIS HAS TO BE ON.  SO THERE.
        #self._dist_filter.SetUseImageSpacing(True)
        
        ScriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
             'itkDanielssonDistanceMapImageFilter' : self._dist_filter})

        self.sync_module_logic_with_config()
        
    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for input_idx in range(len(self.get_input_descriptions())):
            self.set_input(input_idx, None)

        # this will take care of all display thingies
        ScriptedConfigModuleMixin.close(self)
        # and the baseclass close
        ModuleBase.close(self)
            
        # remove all bindings
        del self._dist_filter

    def execute_module(self):
        self._dist_filter.Update()

    def get_input_descriptions(self):
        return ('ITK Image (3D, float)',)

    def set_input(self, idx, inputStream):
        try:
            self._dist_filter.SetInput(inputStream)
        except TypeError, e:
            # deduce the type
            itku = itk_kit.utils
            ss = itku.get_img_type_and_dim_shortstring(inputStream)
            img_type = getattr(itk.Image,ss)
            # try to build a new pipeline (will throw exception if it
            # can't)
            self._create_pipeline(img_type)

            # re-apply config
            self.sync_module_logic_with_config()
            # connect input and hope it works.
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

    def _create_pipeline(self, img_type):
        """Standard pattern to create ITK pipeline according to passed
        image type.
        """
        try:
            d = itk.DanielssonDistanceMapImageFilter[
                    img_type, img_type].New()

        except KeyError, e:
            emsg = 'Could not create DanielssonDist with input type %s. '\
                    'Please try a different input type.' % (ss,)
            raise TypeError, emsg

        # if successful, we can disconnect the old filter and store 
        # the instance (needed for the progress call!)
        if self._dist_filter:
            self._dist_filter.SetInput(None)

        self._dist_filter = d

        # setup progress
        itku = itk_kit.utils
        itku.setupITKObjectProgress(
                self, self._dist_filter, 'DanielssonDistanceMapImageFilter',
                'Calculating distance map.')





        
