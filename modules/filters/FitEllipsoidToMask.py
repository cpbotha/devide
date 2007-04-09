from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import moduleUtils
import vtk
import numpy

class FitEllipsoidToMask(noConfigModuleMixin, moduleBase):
    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)

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

        noConfigModuleMixin.__init__(
            self, {'Module (self)' : self})

        self.sync_module_logic_with_config()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        noConfigModuleMixin.close(self)
        
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
                
        # calculate covariance matrix ##############################
        # we need to give cov a 3 by N matrix, hence the transpose
        points2 = numpy.array(points).transpose()
        covariance = numpy.cov(points2)

        # eigen-analysis (u eigenvalues, v eigenvectors)
        u,v = numpy.linalg.eig(covariance)

        # determine centres (x,y,z)
        cx, cy, cz = numpy.average(points2, 1)

        self._output_dict.update({'u' :u, 'v' : v, 'c' : (cx,cy,cz)})

        # now modify output polydata #########################
        lss = [self._ls1, self._ls2, self._ls3]
        for i in range(len(lss)):
            half_axis = u[i] * 0.5 * v[i]
            ca = numpy.array((cx,cy,cz))
            lss[i].SetPoint1(ca - half_axis)
            lss[i].SetPoint2(ca + half_axis)

        self._append_pd.Update()
        
