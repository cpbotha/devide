import genUtils
from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtk
import vtktud

class MyGlyph3D(scriptedConfigModuleMixin, moduleBase):

    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)


        self._glyph3d = vtktud.vtkMyGlyph3D()
        
        moduleUtils.setupVTKObjectProgress(self, self._glyph3d,
                                           'Making 3D glyphs')
        
                                           
        self._config.scaling = 1.0
        self._config.scalemode = 1.0

        configList = [
            ('Scaling:', 'scaling', 'base:float', 'text',
             'Glyphs will be scaled by this factor.'),
            ('Scalemode:', 'scalemode', 'base:int', 'text',
             'Scaling will occur by scalar, vector direction or magnitude.')]
        scriptedConfigModuleMixin.__init__(self, configList)        
        

        self._viewFrame = self._createWindow(
            {'Module (self)' : self,
             'vtkMyGlyph3D' : self._glyph3d})

        # pass the data down to the underlying logic
        self.config_to_logic()
        # and all the way up from logic -> config -> view to make sure
        self.logic_to_config()
        self.config_to_view()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)

        moduleBase.close(self)
        
        # get rid of our reference
        del self._glyph3d

    def get_input_descriptions(self):
        return ('vtkPolyData',)

    def set_input(self, idx, inputStream):
        self._glyph3d.SetInput(inputStream)

    def get_output_descriptions(self):
        return ('Glyphs (vtkPolyData)', )

    def get_output(self, idx):
        return self._glyph3d.GetOutput()

    def logic_to_config(self):
        self._config.scaling = self._glyph3d.GetScaling()
        self._config.scalemode = self._glyph3d.GetScaleMode()
    
    def config_to_logic(self):
        self._glyph3d.SetScaling(self._config.scaling)
        self._glyph3d.SetScaleMode(self._config.scalemode)
    
    def execute_module(self):
        self._glyph3d.Update()
        


