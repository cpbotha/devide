# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

from module_base import ModuleBase
from module_mixins import NoConfigModuleMixin
import module_utils
import vtk
import numpy

class FitEllipsoidToMask(NoConfigModuleMixin, ModuleBase):
    def __init__(self, module_manager):
        # initialise our base class
        ModuleBase.__init__(self, module_manager)

        self._input_data = None
        self._output_dict = {}

        # polydata pipeline to make crosshairs
        self._ls1 = vtk.vtkLineSource()
        self._ls2 = vtk.vtkLineSource()
        self._ls3 = vtk.vtkLineSource()
        self._append_pd = vtk.vtkAppendPolyData()
        self._append_pd.AddInput(self._ls1.GetOutput())
        self._append_pd.AddInput(self._ls2.GetOutput())
        self._append_pd.AddInput(self._ls3.GetOutput())

        NoConfigModuleMixin.__init__(
            self, {'Module (self)' : self})

        self.sync_module_logic_with_config()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for input_idx in range(len(self.get_input_descriptions())):
            self.set_input(input_idx, None)

        # this will take care of all display thingies
        NoConfigModuleMixin.close(self)
        
    def get_input_descriptions(self):
        return ('VTK image data',)

    def set_input(self, idx, input_stream):
        self._input_data = input_stream

    def get_output_descriptions(self):
        return ('Ellipsoid (eigen-analysis) parameters', 'Crosshairs polydata')

    def get_output(self, idx):
        if idx == 0:
            return self._output_dict
        else:
            return self._append_pd.GetOutput()

    def execute_module(self):
        ii = self._input_data
        if not ii:
            return

        # now we need to iterate through the whole input data
        ii.Update()

        iorigin = ii.GetOrigin()
        ispacing = ii.GetSpacing()
        maxx, maxy, maxz = ii.GetDimensions()

        numpoints = 0
        points = []
        for z in range(maxz):
            wz = z * ispacing[2] + iorigin[2]
            for y in range(maxy):
                wy = y * ispacing[1] + iorigin[1]
                for x in range(maxx):
                    v = ii.GetScalarComponentAsDouble(x,y,z,0)
                    if v > 0.0:
                        wx = x * ispacing[0] + iorigin[0]
                        points.append((wx,wy,wz))
                
        # covariance matrix ##############################

        if len(points) == 0:
            self._output_dict.update({'u' : None, 'v' : None, 'c' : None,
                                      'axis_lengths' : None,
                                      'radius_vectors' : None})
            return

        # determine centre (x,y,z)
        points2 = numpy.array(points)
        centre = numpy.average(points2, 0)
        cx,cy,cz = centre
        
        # subtract centre from all points
        points_c = points2 - centre
        
        covariance = numpy.cov(points_c.transpose())

        # eigen-analysis (u eigenvalues, v eigenvectors)
        u,v = numpy.linalg.eig(covariance)

        # estimate length at 2.0 * standard deviation in both directions
        axis_lengths = [4.0 * numpy.sqrt(eigval) for eigval in u]

        radius_vectors = numpy.zeros((3,3), float)
        for i in range(3):
            radius_vectors[i] = v[i] * axis_lengths[i] / 2.0
            
        self._output_dict.update({'u' :u, 'v' : v, 'c' : (cx,cy,cz),
                                  'axis_lengths' : tuple(axis_lengths),
                                  'radius_vectors' : radius_vectors})

        # now modify output polydata #########################
        lss = [self._ls1, self._ls2, self._ls3]
        for i in range(len(lss)):
            half_axis = radius_vectors[i] #axis_lengths[i] / 2.0 * v[i]
            ca = numpy.array((cx,cy,cz))
            lss[i].SetPoint1(ca - half_axis)
            lss[i].SetPoint2(ca + half_axis)

        self._append_pd.Update()
        
def pca(points):
    """PCA factored out of execute_module and made N-D.  not being used yet.

    points is a list of M N-d tuples.

    returns eigenvalues (u), eigenvectors (v), axis_lengths and
    radius_vectors.
    """
   
    # for a list of M N-d tuples, returns an array with M rows and N
    # columns
    points2 = numpy.array(points)
    # determine centre by averaging over 0th axis (over rows)
    centre = numpy.average(points2, 0)

    # subtract centre from all points
    points_c = points2 - centre
        
    covariance = numpy.cov(points_c.transpose())

    # eigen-analysis (u eigenvalues, v eigenvectors)
    u,v = numpy.linalg.eig(covariance)
   
    # estimate length at 2.0 * standard deviation in both directions
    axis_lengths = [4.0 * numpy.sqrt(eigval) for eigval in u]

    N = len(u)
    radius_vectors = numpy.zeros((N,N), float)
    for i in range(N):
        radius_vectors[i] = v[i] * axis_lengths[i] / 2.0

    output_dict = {'u' :u, 'v' : v, 'c' : centre,
                   'axis_lengths' : tuple(axis_lengths),
                   'radius_vectors' : radius_vectors}

    return output_dict

