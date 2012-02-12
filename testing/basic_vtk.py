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

    def test_vtk_progress_exception_masking(self):
        """Ensure progress events are not masking exceptions.
        """

        import vtk
        import vtkdevide

        def observer_progress(o, e):
            print "DICOM progress %s." % (str(o.GetProgress() * 100.0),)

        r = vtkdevide.vtkDICOMVolumeReader()
        r.AddObserver("ProgressEvent", observer_progress)

        try:
            r.Update()
        except RuntimeError, e:
            pass
        else:
            self.fail('ProgressEvent handler masked RuntimeError.')

    def test_vtk_pyexception_deadlock(self):
        """Test if VTK has been patched to release the GIL during all
        VTK method calls.
        """

        import vtk
        # this gives floats by default
        s = vtk.vtkImageGridSource()
        c1 = vtk.vtkImageCast()
        c1.SetOutputScalarTypeToShort()
        c1.SetInput(s.GetOutput())
        c2 = vtk.vtkImageCast()
        c2.SetOutputScalarTypeToFloat()
        c2.SetInput(s.GetOutput())

        m = vtk.vtkImageMathematics()

        # make sure we are multi-threaded
        if m.GetNumberOfThreads() < 2:
            m.SetNumberOfThreads(2)
        m.SetInput1(c1.GetOutput())
        m.SetInput2(c2.GetOutput())

        # without the patch, this call will deadlock forever
        try:
            # with the patch this should generate a RuntimeError
            m.Update()
        except RuntimeError:
            pass
        else:
            self.fail(
            'Multi-threaded error vtkImageMathematics did not raise '
            'exception.')


def get_suite(devide_testing):
    devide_app = devide_testing.devide_app
    
    mm = devide_app.get_module_manager()

    basic_vtk_suite = unittest.TestSuite()

    if 'vtk_kit' not in mm.module_kits.module_kit_list:
        return basic_vtk_suite

    t = BasicVTKTest('test_vtk_exceptions')
    basic_vtk_suite.addTest(t)

    t = BasicVTKTest('test_vtk_progress_exception_masking')
    basic_vtk_suite.addTest(t)

    t = BasicVTKTest('test_vtk_pyexception_deadlock')
    basic_vtk_suite.addTest(t)

    return basic_vtk_suite

    
    
