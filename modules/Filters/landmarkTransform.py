# landmarkTransform.py copyright (c) 2003 by Charl P. Botha <cpbotha@ieee.org>
# $Id: landmarkTransform.py,v 1.1 2003/10/15 11:25:32 cpbotha Exp $
# see module documentation

import genUtils
from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import moduleUtils
#from wxPython.wx import *
import vtk

class landmarkTransform(moduleBase, noConfigModuleMixin):
    """The landmarkTransform will calculate a 4x4 linear transform that maps
    from a set of source landmarks to a set of target landmarks.

    The mapping is optimised with a least-squares metric.  You have to supply
    two sets of points, all points in the source set have to be named
    'Source' and all the points in the target set have to be named 'Target'.

    This module will supply a vtkTransform at its first output and a 4x4
    vtk Matrix at its second output.  By connecting the vtkTransform to
    a transformPolyData module, you'll be able to perform the actual
    transformation.
    """

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)
        noConfigModuleMixin.__init__(self)

        self._landmarkTransform = vtk.vtkLandmarkTransform()
        moduleUtils.setupVTKObjectProgress(self, self._landmarkTransform,
                                           'Optimising transform')

        self._viewFrame = self._createViewFrame(
            {'vtkLandmarkTransform': self._landmarkTransform})

        self.configToLogic()
        self.syncViewWithLogic()


        
