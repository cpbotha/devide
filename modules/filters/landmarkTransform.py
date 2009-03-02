# landmark_transform.py copyright (c) 2003 by Charl P. Botha <cpbotha@ieee.org>
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

        self._input_points = [None, None]

        self._source_landmarks = None
        self._target_landmarks = None

        self._config.mode = 'Rigid'

        configList = [('Transformation mode:', 'mode', 'base:str', 'choice',
                       'Rigid: rotation + translation;\n'
                       'Similarity: rigid + isotropic scaling\n'
                       'Affine: rigid + scaling + shear',
                       ('Rigid', 'Similarity', 'Affine'))]

        self._landmark_transform = vtk.vtkLandmarkTransform()

        ScriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
             'vtkLandmarkTransform': self._landmark_transform})

        self.sync_module_logic_with_config()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for input_idx in range(len(self.get_input_descriptions())):
            self.set_input(input_idx, None)

        # this will take care of all display thingies
        ScriptedConfigModuleMixin.close(self)
        
        # get rid of our reference
        del self._landmark_transform

    def get_input_descriptions(self):
        return ('Source and/or Target Points', 
        'Source and/or Target Points')

    def set_input(self, idx, input_stream):
        if input_stream is not self._input_points[idx]:

            if input_stream == None:
                self._input_points[idx] = None

            elif hasattr(input_stream, 'devideType') and \
                 input_stream.devideType == 'namedPoints':

                self._input_points[idx] = input_stream

            else:
                raise TypeError, 'This input requires a named points type.'

    def get_output_descriptions(self):
        return ('vtkTransform',)

    def get_output(self, idx):
            return self._landmark_transform

    def logic_to_config(self):
        mas = self._landmark_transform.GetModeAsString()
        if mas == 'RigidBody':
            mas = 'Rigid'
        self._config.mode = mas
    
    def config_to_logic(self):
        if self._config.mode == 'Rigid':
            self._landmark_transform.SetModeToRigidBody()
        elif self._config.mode == 'Similarity':
            self._landmark_transform.SetModeToSimilarity()
        else:
            self._landmark_transform.SetModeToAffine()
    
    def execute_module(self):
        self._sync_with_input_points()
        self._landmark_transform.Update()

    def _sync_with_input_points(self):
        # the points have changed, let's see if they really have

        if not (self._input_points[0] or self._input_points[1]):
            return

        all_points = self._input_points[0] + self._input_points[1]
       

        # we want i['world'] eventually
        temp_source_points = [i for i in all_points
                              if i['name'].lower().startswith('source')]
        temp_target_points = [i for i in all_points
                              if i['name'].lower().startswith('target')]

        # now put both source and target points in dict keyed on short
        # name
        slen = len('source')
        sdict = {}
        tdict = {}
        for dict, points in [(sdict, temp_source_points), (tdict,
            temp_target_points)]:
            for point in points:
                # turn 'source moo maa ' into 'moo maa'
                name = point['name'][slen:].strip()
                # stuff world position in dict keyed by name
                dict[name] = point['world']

        # use this as decorator list
        snames = sdict.keys()
        snames.sort()

        temp_source_landmarks = [sdict[name] for name in snames]
        try:
            temp_target_landmarks = [tdict[name] for name in snames]
        except KeyError:
            raise RuntimeError("There is no target point named '%s'" %
                    (name))


        if temp_source_landmarks != self._source_landmarks or \
           temp_target_landmarks != self._target_landmarks:

            self._source_landmarks = temp_source_landmarks
            self._target_landmarks = temp_target_landmarks

            source_landmarks = vtk.vtkPoints()
            target_landmarks = vtk.vtkPoints()
            landmarkPairs = ((self._source_landmarks, source_landmarks),
                             (self._target_landmarks, target_landmarks))
            
            for lmp in landmarkPairs:
                lmp[1].SetNumberOfPoints(len(lmp[0]))
                for pointIdx in range(len(lmp[0])):
                    lmp[1].SetPoint(pointIdx, lmp[0][pointIdx])
                             
            self._landmark_transform.SetSourceLandmarks(source_landmarks)
            self._landmark_transform.SetTargetLandmarks(target_landmarks)
            
        
        
