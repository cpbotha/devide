# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

from module_base import ModuleBase
from module_mixins import ScriptedConfigModuleMixin
import module_utils
import vtk
import input_array_choice_mixin
reload(input_array_choice_mixin)
from input_array_choice_mixin import InputArrayChoiceMixin

# scale vector glyph with scalar, vector magnitude, or separately for each
# direction (using vector components), or don't scale at all
# default is SCALE_BY_VECTOR = 1
glyphScaleMode = ['SCALE_BY_SCALAR', 'SCALE_BY_VECTOR',
                   'SCALE_BY_VECTORCOMPONENTS', 'DATA_SCALING_OFF']

glyphScaleModeTexts = ['Scale by scalar attribute',
                       'Scale by vector magnitude',
                       'Scale with x,y,z vector components',
                       'Use only scale factor']

# colour by scale (magnitude of scaled vector), by scalar or by vector
# default: COLOUR_BY_VECTOR = 1
glyphColourMode = ['COLOUR_BY_SCALE', 'COLOUR_BY_SCALAR', 'COLOUR_BY_VECTOR']

glyphColourModeTexts = ['Colour by scale', 'Colour by scalar attribute',
                        'Colour by vector magnitude']

# which data should be used for scaling, orientation and indexing
# default: USE_VECTOR = 0
glyphVectorMode = ['USE_VECTOR', 'USE_NORMAL', 'VECTOR_ROTATION_OFF']
glyphVectorModeTexts = ['Use vector', 'Use normal', 'Do not orient']
                       

# we can use different glyph types in the same visualisation
# default: INDEXING_OFF = 0
# (we're not going to use this right now)
glyphIndexMode = ['INDEXING_OFF', 'INDEXING_BY_SCALAR', 'INDEXING_BY_VECTOR']


class glyphs(ScriptedConfigModuleMixin, InputArrayChoiceMixin, ModuleBase):
    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)
        InputArrayChoiceMixin.__init__(self)

        self._config.scaling = True
        self._config.scaleFactor = 1
        self._config.scaleMode = glyphScaleMode.index('SCALE_BY_VECTOR')
        self._config.colourMode = glyphColourMode.index('COLOUR_BY_VECTOR')
        self._config.vectorMode = glyphVectorMode.index('USE_VECTOR')
        self._config.mask_on_ratio = 5
        self._config.mask_random = True


        configList = [
            ('Scale glyphs:', 'scaling', 'base:bool', 'checkbox',
             'Should the size of the glyphs be scaled?'),
            ('Scale factor:', 'scaleFactor', 'base:float', 'text',
             'By how much should the glyph size be scaled if scaling is '
             'active?'),
            ('Scale mode:', 'scaleMode', 'base:int', 'choice',
             'Should scaling be performed by vector, scalar or only factor?',
             glyphScaleModeTexts),
            ('Colour mode:', 'colourMode', 'base:int', 'choice',
             'Colour is determined based on scalar or vector magnitude.',
             glyphColourModeTexts),
            ('Vector mode:', 'vectorMode', 'base:int', 'choice',
             'Should vectors or normals be used for scaling and orientation?',
             glyphVectorModeTexts),
            ('Vectors selection:', 'vectorsSelection', 'base:str', 'choice',
             'The attribute that will be used as vectors for the warping.',
             (input_array_choice_mixin.DEFAULT_SELECTION_STRING,)),
            ('Mask on ratio:', 'mask_on_ratio', 'base:int', 'text',
             'Every Nth point will be glyphed.'),
            ('Random masking:', 'mask_random', 'base:bool', 'checkbox',
             'Pick random distribution of Nth points.')]

        self._mask_points = vtk.vtkMaskPoints()
        module_utils.setup_vtk_object_progress(self,
                self._mask_points, 'Masking points.')

        self._glyphFilter = vtk.vtkGlyph3D()
        as = vtk.vtkArrowSource()
        self._glyphFilter.SetSource(0, as.GetOutput())

        self._glyphFilter.SetInput(self._mask_points.GetOutput())
        
        module_utils.setup_vtk_object_progress(self, self._glyphFilter,
                                           'Creating glyphs.')

        ScriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
             'vtkGlyph3D' : self._glyphFilter})

        self.sync_module_logic_with_config()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for input_idx in range(len(self.get_input_descriptions())):
            self.set_input(input_idx, None)

        # this will take care of all display thingies
        ScriptedConfigModuleMixin.close(self)
        
        # get rid of our reference
        del self._mask_points
        del self._glyphFilter

    def execute_module(self):
        self._glyphFilter.Update()
        if self.view_initialised:
            choice = self._getWidget(5)
            self.iac_execute_module(self._glyphFilter, choice, 1)
        

    def get_input_descriptions(self):
        return ('VTK Vector dataset',)

    def set_input(self, idx, inputStream):
        self._mask_points.SetInput(inputStream)

    def get_output_descriptions(self):
        return ('3D glyphs',)

    def get_output(self, idx):
        return self._glyphFilter.GetOutput()

    def logic_to_config(self):
        self._config.scaling = bool(self._glyphFilter.GetScaling())
        self._config.scaleFactor = self._glyphFilter.GetScaleFactor()
        self._config.scaleMode = self._glyphFilter.GetScaleMode()
        self._config.colourMode = self._glyphFilter.GetColorMode()
        self._config.vectorMode = self._glyphFilter.GetVectorMode()

        self._config.mask_on_ratio = \
                             self._mask_points.GetOnRatio()
        self._config.mask_random = bool(self._mask_points.GetRandomMode())

        # this will extract the possible choices
        self.iac_logic_to_config(self._glyphFilter, 1)

    def config_to_view(self):
        # first get our parent mixin to do its thing
        ScriptedConfigModuleMixin.config_to_view(self)

        # the vector choice is the second configTuple
        choice = self._getWidget(5)
        self.iac_config_to_view(choice)

        
    def config_to_logic(self):
        self._glyphFilter.SetScaling(self._config.scaling)
        self._glyphFilter.SetScaleFactor(self._config.scaleFactor)
        self._glyphFilter.SetScaleMode(self._config.scaleMode)
        self._glyphFilter.SetColorMode(self._config.colourMode)
        self._glyphFilter.SetVectorMode(self._config.vectorMode)
        self._mask_points.SetOnRatio(self._config.mask_on_ratio)
        self._mask_points.SetRandomMode(int(self._config.mask_random))

        # it seems that array_idx == 1 refers to vectors
        # array_idx 0 gives me only the x-component of multi-component
        # arrays
        self.iac_config_to_logic(self._glyphFilter, 1)

