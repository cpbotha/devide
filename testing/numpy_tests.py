import sys
import unittest

class NumPyTest(unittest.TestCase):
    def test_import_mixing(self):
        """Test for bug where packaged numpy and installed numpy would
        conflict, causing errors.
        """
        import numpy

        try:
            na = numpy.array([0,0,0])
            print na
        except Exception, e:
            self.fail('numpy.array() cast raises exception: %s' %
                    (str(e),)) 
        else:
            pass


def get_suite(devide_testing):
    devide_app = devide_testing.devide_app
    
    # both of these tests require wx
    mm = devide_app.get_module_manager()

    numpy_suite = unittest.TestSuite()

    if 'numpy_kit' in mm.module_kits.module_kit_list:
        t = NumPyTest('test_import_mixing')
        t._devide_app = devide_app
        t._devide_testing = devide_testing
        numpy_suite.addTest(t)
        
    return numpy_suite


