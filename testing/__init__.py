# testing.__init__.py copyright 2006 by Charl P. Botha http://cpbotha.net/
# $Id$
# this drives the devide unit testing.  neat huh?

import os
import time
import unittest

from testing import basic_vtk
from testing import basic_wx
from testing import graph_editor
from testing import matplotlib_tests

module_list = [basic_vtk, basic_wx, graph_editor, matplotlib_tests]
for m in module_list:
    reload(m)


# ----------------------------------------------------------------------------
class DeVIDETesting:
    def __init__(self, devide_app):

        self.devide_app = devide_app
        
        suite_list = [basic_vtk.get_suite(self),
                      basic_wx.get_suite(self),
                      graph_editor.get_suite(self),
                      matplotlib_tests.get_suite(self)]

        self.main_suite = unittest.TestSuite(tuple(suite_list))
        
    def runAllTests(self):
        runner = unittest.TextTestRunner()
        runner.run(self.main_suite)

    def runSomeTest(self):
        some_suite = matplotlib_tests.get_suite(self)

        runner = unittest.TextTestRunner()
        runner.run(some_suite)

    def get_images_dir(self):
        """Return full path of directory with test images.
        """

        return os.path.join(os.path.dirname(__file__), 'images')
        
    def compare_png_images(self, image1_filename, image2_filename,
                           threshold=16):

        """Compare two PNG images on disc.  No two pixels may differ with more
        than the default threshold.
        """

        import vtk

        r1 = vtk.vtkPNGReader()
        r1.SetFileName(image1_filename)
        r1.Update()
        # sometimes PNG files have an ALPHA component we have to chuck away
        ec1 = vtk.vtkImageExtractComponents()
        ec1.SetComponents(0,1,2)
        ec1.SetInput(r1.GetOutput())
        
        r2 = vtk.vtkPNGReader()
        r2.SetFileName(image2_filename)
        r2.Update()
        # sometimes PNG files have an ALPHA component we have to chuck away
        ec2 = vtk.vtkImageExtractComponents()
        ec2.SetComponents(0,1,2)
        ec2.SetInput(r2.GetOutput())

        idiff = vtk.vtkImageDifference()
        idiff.SetThreshold(threshold)

        idiff.SetImage(ec1.GetOutput())
        idiff.SetInputConnection(ec2.GetOutputPort())

        idiff.Update()

        return idiff.GetThresholdedError()
        

        
