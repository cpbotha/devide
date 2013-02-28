__author__ = 'Francois'

# PerturbPolyPoints.py by Francois Malan - 2012-12-06
# Randomly perturbs each polydata vertex by a uniformly sampled magnitude and random direction

from module_base import ModuleBase
from module_mixins import ScriptedConfigModuleMixin
import vtk
import numpy
import math
import random

class PerturbPolyPoints(ScriptedConfigModuleMixin, ModuleBase):

    def __init__(self, module_manager):
        # initialise our base class
        ModuleBase.__init__(self, module_manager)

        self.sync_module_logic_with_config()

        self._config.perturbation_magnitude = 0.15    #tolerance (distance) for determining if a point lies on a plane
        self._config.use_gaussian = False

        config_list = [
            ('Perturbation Magnitude:', 'perturbation_magnitude', 'base:float', 'text',
             'The magnitude of the perturbation (upperlimit for uniform distribution, or twice the standard deviation for Gaussian distribution). '
             'The 2x scaling ensures that the typical perturbation magnitudes are similar.'),
            ('Gaussian distribution:', 'use_gaussian', 'base:bool', 'checkbox',
             'Should a Gaussian distribution be used instead of a uniform distribution?'),
            ]

        ScriptedConfigModuleMixin.__init__(
            self, config_list,
            {'Module (self)' : self})

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for input_idx in range(len(self.get_input_descriptions())):
            self.set_input(input_idx, None)

        # this will take care of GUI
        ScriptedConfigModuleMixin.close(self)

    def set_input(self, idx, input_stream):
        if idx == 0:
            self.source_poly = input_stream

    def get_input_descriptions(self):
        return ('vtkPolyData', )

    def get_output_descriptions(self):
        return ('vtkPolyData', )

    def get_output(self, idx):
        return self.output_poly

    def _normalize(self, vector):
        length = math.sqrt(numpy.dot(vector, vector))
        if length == 0:
            return numpy.array([1,0,0])
        return vector / length

    def _perturb_points(self, poly, magnitude):
        assert isinstance(poly, vtk.vtkPolyData)

        points = poly.GetPoints()
        n = poly.GetNumberOfPoints()

        for i in range(n):
            point = points.GetPoint(i)
            vector = numpy.array([random.random(),random.random(),random.random()]) - 0.5
            direction = self._normalize(vector)
            magnitude = 0.0
            if not self._config.use_gaussian:
                magnitude = random.random() * self._config.perturbation_magnitude
            else:
                magnitude = random.gauss(0.0, self._config.perturbation_magnitude/2.0)
            vector = direction * magnitude
            newpoint = numpy.array(point) + vector
            points.SetPoint(i, (newpoint[0],newpoint[1],newpoint[2]))

    def logic_to_config(self):
        pass

    def config_to_logic(self):
        pass

    def execute_module(self):
        self.output_poly = vtk.vtkPolyData()
        self.output_poly.DeepCopy(self.source_poly)

        self._perturb_points(self.output_poly, self._config.perturbation_magnitude)