"""Module to test basic DeVIDE functionality.
"""

import unittest

class BasicVTKTest(unittest.TestCase):
    def test_vtk_exceptions(self):
        """Test if VTK has been patched with our VTK error to Python exception
        patch.
        """

        import vtk
        a = vtk.vtkXMLImageDataReader()
        a.SetFileName('blata22 hello')
        b = vtk.vtkMarchingCubes()
        b.SetInput(a.GetOutput())

        try:
            b.Update()
        except RuntimeError, e:
            self.failUnless(str(e).startswith('ERROR'))

        else:
            self.fail('VTK object did not raise Python exception.')


def get_suite(devide_testing):
    devide_app = devide_testing.devide_app
    
    mm = devide_app.get_module_manager()

    basic_vtk_suite = unittest.TestSuite()

    if 'vtk_kit' not in mm.module_kits.module_kit_list:
        return basic_vtk_suite

    t = BasicVTKTest('test_vtk_exceptions')
    basic_vtk_suite.addTest(t)

    return basic_vtk_suite

    
    
