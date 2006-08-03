"""Module to test basic DeVIDE functionality.
"""

import unittest

class PythonShellTest(unittest.TestCase):
    def test_python_shell(self):
        """Test if PythonShell can be opened successfully.
        """
        self._devide_app.get_interface()._handler_menu_python_shell(None)
        self.failUnless(self._devide_app.get_interface()._python_shell.\
                        _frame.IsShown())


class HelpContentsTest(unittest.TestCase):
    def test_help_contents(self):
        """Test if Help Contents can be opened successfully.
        """
        self._devide_app.get_interface()._handlerHelpContents(None)
        self.failUnless(
            self._devide_app.get_interface()._helpClass._htmlHelpController.\
            GetFrame().IsShown())

def get_suite(devide_app):
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

    
    
