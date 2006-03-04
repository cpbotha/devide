"""Module to test basic DeVIDE functionality.
"""

import unittest

# fixme: these are WX-interface-specific tests and should be treated as such.
class PythonShellTest(unittest.TestCase):
    def test_python_shell(self):
        """Test if PythonShell can be opened successfully.
        """
        self._devide_app.get_interface()._handlerMenuPythonShell(None)
        self.failUnless(self._devide_app.get_interface()._pythonShell.\
                        _psFrame.IsShown())


class HelpContentsTest(unittest.TestCase):
    def test_help_contents(self):
        """Test if Help Contents can be opened successfully.
        """
        self._devide_app.get_interface()._handlerHelpContents(None)
        self.failUnless(
            self._devide_app.get_interface()._helpClass._htmlHelpController.\
            GetFrame().IsShown())

def get_suite(devide_app):
    basic_suite = unittest.TestSuite()
    
    t = PythonShellTest('test_python_shell')
    t._devide_app = devide_app
    basic_suite.addTest(t)

    t = HelpContentsTest('test_help_contents')
    t._devide_app = devide_app
    basic_suite.addTest(t)

    return basic_suite

    
    
