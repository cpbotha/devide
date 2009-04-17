# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

from module_base import ModuleBase
from module_mixins import ScriptedConfigModuleMixin
import module_utils
import vtk
import input_array_choice_mixin # need this for constants
reload(input_array_choice_mixin)
from input_array_choice_mixin import InputArrayChoiceMixin

class warpPoints(ScriptedConfigModuleMixin, InputArrayChoiceMixin,
                 ModuleBase):
    
    _defaultVectorsSelectionString = 'Default Active Vectors'
    _userDefinedString = 'User Defined'

    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)
        InputArrayChoiceMixin.__init__(self)
        
        self._config.scaleFactor = 1

        configList = [
            ('Scale factor:', 'scaleFactor', 'base:float', 'text',
             'The warping will be scaled by this factor'),
            ('Vectors selection:', 'vectorsSelection', 'base:str', 'choice',
             'The attribute that will be used as vectors for the warping.',
             (self._defaultVectorsSelectionString, self._userDefinedString))]

        self._warpVector = vtk.vtkWarpVector()

        ScriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
             'vtkWarpVector' : self._warpVector})
        
        module_utils.setup_vtk_object_progress(self, self._warpVector,
                                           'Warping points.')
        

        self.sync_module_logic_with_config()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for input_idx in range(len(self.get_input_descriptions())):
            self.set_input(input_idx, None)

        # this will take care of all display thingies
        ScriptedConfigModuleMixin.close(self)
        
        # get rid of our reference
        del self._warpVector

    def execute_module(self):
        self._warpVector.Update()

        if self.view_initialised:
            # second element in configuration list
            choice = self._getWidget(1)
            self.iac_execute_module(self._warpVector, choice, 0)

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
        self.iac_logic_to_config(self._warpVector, 0)

    def config_to_view(self):
        # first get our parent mixin to do its thing
        ScriptedConfigModuleMixin.config_to_view(self)

        # the vector choice is the second configTuple
        choice = self._getWidget(1)
        self.iac_config_to_view(choice)

    def config_to_logic(self):
        self._warpVector.SetScaleFactor(self._config.scaleFactor)

        self.iac_config_to_logic(self._warpVector, 0)

