from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtk
import vtkdevide


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


class glyphs(scriptedConfigModuleMixin, moduleBase):
    """Visualise vector field with glyphs.

    $Revision: 1.4 $
    """

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        self._config.scaling = True
        self._config.scaleFactor = 1
        self._config.scaleMode = glyphScaleMode.index('SCALE_BY_VECTOR')
        self._config.colourMode = glyphColourMode.index('COLOUR_BY_VECTOR')
        self._config.vectorMode = glyphVectorMode.index('USE_VECTOR')
        self._config.maskPoints = True
        self._config.maskMax = 5000
        self._config.maskRandom = True


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
            ('Mask points:', 'maskPoints', 'base:bool', 'checkbox',
             'Only a selection of the input points will be glyphed.'),
            ('Number of masked points:', 'maskMax', 'base:int', 'text',
             'If masking is active, this is the maximum number of input '
             'points that will be masked.'),
            ('Random masking:', 'maskRandom', 'base:bool', 'checkbox',
             'If masking is active, pick random points.')]

        scriptedConfigModuleMixin.__init__(self, configList)

        self._glyphFilter = vtkdevide.vtkPVGlyphFilter()
        as = vtk.vtkArrowSource()
        self._glyphFilter.SetSource(0, as.GetOutput())
        
        moduleUtils.setupVTKObjectProgress(self, self._glyphFilter,
                                           'Creating glyphs.')
        

        self._createWindow(
            {'Module (self)' : self,
             'vtkPVGlyphFilter' : self._glyphFilter})

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
        
        # get rid of our reference
        del self._glyphFilter

    def executeModule(self):
        self._glyphFilter.Update()
        

    def getInputDescriptions(self):
        return ('VTK Vector dataset',)

    def setInput(self, idx, inputStream):
        self._glyphFilter.SetInput(inputStream)

    def getOutputDescriptions(self):
        return ('3D glyphs',)

    def getOutput(self, idx):
        return self._glyphFilter.GetOutput()

    def logicToConfig(self):
        self._config.scaling = bool(self._glyphFilter.GetScaling())
        self._config.scaleFactor = self._glyphFilter.GetScaleFactor()
        self._config.scaleMode = self._glyphFilter.GetScaleMode()
        self._config.colourMode = self._glyphFilter.GetColorMode()
        self._config.vectorMode = self._glyphFilter.GetVectorMode()
        self._config.maskPoints = bool(self._glyphFilter.GetUseMaskPoints())
        self._config.maskMax = \
                             self._glyphFilter.GetMaximumNumberOfPoints()
        self._config.maskRandom = bool(self._glyphFilter.GetRandomMode())
    
    def configToLogic(self):
        self._glyphFilter.SetScaling(self._config.scaling)
        self._glyphFilter.SetScaleFactor(self._config.scaleFactor)
        self._glyphFilter.SetScaleMode(self._config.scaleMode)
        self._glyphFilter.SetColorMode(self._config.colourMode)
        self._glyphFilter.SetVectorMode(self._config.vectorMode)
        self._glyphFilter.SetUseMaskPoints(self._config.maskPoints)
        self._glyphFilter.SetMaximumNumberOfPoints(self._config.maskMax)
        self._glyphFilter.SetRandomMode(self._config.maskRandom)
