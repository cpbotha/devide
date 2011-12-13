# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

from module_base import ModuleBase
from module_mixins import ScriptedConfigModuleMixin
import module_utils
import vtk

class ICPTransform(ScriptedConfigModuleMixin, ModuleBase):

    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        # this has no progress feedback
        self._icp = vtk.vtkIterativeClosestPointTransform()

        self._config.max_iterations = 50
        self._config.mode = 'RigidBody' 
        self._config.align_centroids = True

        config_list = [
            ('Transformation mode:', 'mode', 'base:str', 'choice',
              'Rigid: rotation + translation;\n'
              'Similarity: rigid + isotropic scaling\n'
              'Affine: rigid + scaling + shear',
              ('RigidBody', 'Similarity', 'Affine')),
            ('Maximum number of iterations:', 'max_iterations',
                'base:int', 'text',
             'Maximum number of iterations for ICP.'),
            ('Align centroids before start', 'align_centroids', 'base:bool', 'checkbox',
             'Align centroids before iteratively optimizing closest points? (required for large relative translations)')
            ]
             
        ScriptedConfigModuleMixin.__init__(
            self, config_list,
            {'Module (self)' : self,
             'vtkIterativeClosestPointTransform' : self._icp})

        self.sync_module_logic_with_config()

    def close(self):
        ScriptedConfigModuleMixin.close(self)

        # get rid of our reference
        del self._icp

        ModuleBase.close(self)

    def get_input_descriptions(self):
        return ('source vtkPolyData', 'target vtkPolyData')
    
    def set_input(self, idx, input_stream):
        if idx == 0:
            self._icp.SetSource(input_stream)
        else:
            self._icp.SetTarget(input_stream)
    
    def get_output_descriptions(self):
        return ('Linear transform',)
    
    def get_output(self, idx):
        return self._icp

    def logic_to_config(self):
        self._config.mode = \
                self._icp.GetLandmarkTransform().GetModeAsString()
        self._config.max_iterations = \
                self._icp.GetMaximumNumberOfIterations()
        self._config.align_centroids = self._icp.GetStartByMatchingCentroids()
    
    def config_to_logic(self):
        lmt = self._icp.GetLandmarkTransform()
        if self._config.mode == 'RigidBody':
            lmt.SetModeToRigidBody()
        elif self._config.mode == 'Similarity':
            lmt.SetModeToSimilarity()
        else:
            lmt.SetModeToAffine()

        self._icp.SetMaximumNumberOfIterations(
                self._config.max_iterations)
                
        self._icp.SetStartByMatchingCentroids(self._config.align_centroids)

    def execute_module(self):
        self._module_manager.set_progress(
                10, 'Starting ICP.')
        self._icp.Update()
        self._module_manager.set_progress(
                100, 'ICP complete.')
        
