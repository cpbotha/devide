from module_base import ModuleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtk
from input_array_choice_mixin import InputArrayChoiceMixin

class warpPoints(InputArrayChoiceMixin, scriptedConfigModuleMixin,
                 ModuleBase):
    
    _defaultVectorsSelectionString = 'Default Active Vectors'
    _userDefinedString = 'User Defined'

    def __init__(self, moduleManager):
        ModuleBase.__init__(self, moduleManager)
        InputArrayChoiceMixin.__init__(self)
        
        self._config.scaleFactor = 1

        configList = [
            ('Scale factor:', 'scaleFactor', 'base:float', 'text',
             'The warping will be scaled by this factor'),
            ('Vectors selection:', 'vectorsSelection', 'base:str', 'choice',
             'The attribute that will be used as vectors for the warping.',
             (self._defaultVectorsSelectionString, self._userDefinedString))]

        self._warpVector = vtk.vtkWarpVector()

        scriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
             'vtkWarpVector' : self._warpVector})
        
        moduleUtils.setupVTKObjectProgress(self, self._warpVector,
                                           'Warping points.')
        

        self.sync_module_logic_with_config()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)
        
        # get rid of our reference
        del self._warpVector

    def execute_module(self):
        self._warpVector.Update()

    def get_input_descriptions(self):
        return ('VTK points/polydata with vector attribute',)

    def set_input(self, idx, inputStream):
        self._warpVector.SetInput(inputStream)

    def get_output_descriptions(self):
        return ('Warped data',)

    def get_output(self, idx):
        # we only return something if we have something
        if self._warpVector.GetNumberOfInputConnections(0):
            return self._warpVector.GetOutput()
        else:
            return None


    def logic_to_config(self):
        self._config.scaleFactor = self._warpVector.GetScaleFactor()

        # this will extract the possible choices
        InputArrayChoiceMixin.logic_to_config(self, self._warpVector)

    def config_to_view(self):
        # first get our parent mixin to do its thing
        scriptedConfigModuleMixin.config_to_view(self)

        # the vector choice is the second configTuple
        choice = self._getWidget(1)
        InputArrayChoiceMixin.config_to_view(self, choice)

    def config_to_logic(self):
        self._warpVector.SetScaleFactor(self._config.scaleFactor)

        InputArrayChoiceMixin.config_to_logic(self, self._warpVector)

