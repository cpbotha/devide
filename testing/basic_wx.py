"""Module to test basic DeVIDE functionality.
"""

import unittest

class PythonShellTest(unittest.TestCase):
    def test_python_shell(self):
        """Test if PythonShell can be opened successfully.
        """
        iface = self._devide_app.get_interface()
        iface._handler_menu_python_shell(None)
        self.failUnless(iface._python_shell._frame.IsShown())
        iface._python_shell._frame.Show(False)
        


class HelpContentsTest(unittest.TestCase):
    def test_help_contents(self):
        """Test if Help Contents can be opened successfully.
        """
        self._devide_app.get_interface()._handlerHelpContents(None)
        hc = self._devide_app.get_interface()._help_class

        if hasattr(hc, '_htmlHelpController'):
            self.failUnless(
                hc._htmlHelpController.GetFrame().IsShown())
        else:
            # this is windows, looking for CHM thingy
            self.failUnless(
                    hc._w32h_hh)

def get_suite(devide_testing):
    devide_app = devide_testing.devide_app
    
    # both of these tests require wx
    mm = devide_app.get_module_manager()

    basic_suite = unittest.TestSuite()

    if 'wx_kit' in mm.module_kits.module_kit_list:
        t = PythonShellTest('test_python_shell')
        t._devide_app = devide_app
        basic_suite.addTest(t)

        t = HelpContentsTest('test_help_contents')
        t._devide_app = devide_app
        basic_suite.addTest(t)

    return basic_suite

    
    
