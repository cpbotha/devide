# landmarkTransform.py copyright (c) 2003 by Charl P. Botha <cpbotha@ieee.org>
# $Id$
# see module documentation

import gen_utils
from module_base import ModuleBase
from module_mixins import ScriptedConfigModuleMixin
import module_utils
import vtk

class landmarkTransform(ScriptedConfigModuleMixin, ModuleBase):

    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        self._inputPoints = None
        self._sourceLandmarks = None
        self._targetLandmarks = None

        self._config.mode = 'Rigid'

        configList = [('Transformation mode:', 'mode', 'base:str', 'choice',
                       'Rigid: rotation + translation;\n'
                       'Similarity: rigid + isotropic scaling\n'
                       'Affine: rigid + scaling + shear',
                       ('Rigid', 'Similarity', 'Affine'))]

        self._landmarkTransform = vtk.vtkLandmarkTransform()

        ScriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
             'vtkLandmarkTransform': self._landmarkTransform})

        self.sync_module_logic_with_config()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        ScriptedConfigModuleMixin.close(self)
        
        # get rid of our reference
        del self._landmarkTransform

    def get_input_descriptions(self):
        return ('Source and Target Points',)

    def set_input(self, idx, inputStream):
        if inputStream is not self._inputPoints:

            if inputStream == None:
                self._inputPoints = None

            elif hasattr(inputStream, 'devideType') and \
                 inputStream.devideType == 'namedPoints':

                self._inputPoints = inputStream

            else:
                raise TypeError, 'This input requires a named points type.'

    def get_output_descriptions(self):
        return ('vtkTransform',)

    def get_output(self, idx):
            return self._landmarkTransform

    def logic_to_config(self):
        mas = self._landmarkTransform.GetModeAsString()
        if mas == 'RigidBody':
            mas = 'Rigid'
        self._config.mode = mas
    
    def config_to_logic(self):
        if self._config.mode == 'Rigid':
            self._landmarkTransform.SetModeToRigidBody()
        elif self._config.mode == 'Similarity':
            self._landmarkTransform.SetModeToSimilarity()
        else:
            self._landmarkTransform.SetModeToAffine()
    
    def execute_module(self):
        self._sync_with_input_points()
        self._landmarkTransform.Update()

    def _sync_with_input_points(self):
        # the points have changed, let's see if they really have

        if not self._inputPoints:
            return
        
        tempSourceLandmarks = [i['world'] for i in self._inputPoints
                               if i['name'].lower().startswith('source')]
        tempTargetLandmarks = [i['world'] for i in self._inputPoints
                               if i['name'].lower().startswith('target')]

        print "hi there"
        
        if tempSourceLandmarks != self._sourceLandmarks or \
           tempTargetLandmarks != self._targetLandmarks:

            print "seems like I have to update"

            if len(tempSourceLandmarks) != len(tempTargetLandmarks):
                raise Exception(
                    "landmarkTransform: Your 'Source' landmark set and "
                    "'Target' landmark set should be of equal size.")

            else:
                self._sourceLandmarks = tempSourceLandmarks
                self._targetLandmarks = tempTargetLandmarks

                sourceLandmarks = vtk.vtkPoints()
                targetLandmarks = vtk.vtkPoints()
                landmarkPairs = ((self._sourceLandmarks, sourceLandmarks),
                                 (self._targetLandmarks, targetLandmarks))
                
                for lmp in landmarkPairs:
                    lmp[1].SetNumberOfPoints(len(lmp[0]))
                    for pointIdx in range(len(lmp[0])):
                        lmp[1].SetPoint(pointIdx, lmp[0][pointIdx])
                                 
                self._landmarkTransform.SetSourceLandmarks(sourceLandmarks)
                self._landmarkTransform.SetTargetLandmarks(targetLandmarks)
                
        
        
