"""Module to test basic DeVIDE functionality.
"""

import unittest

class PythonShellTest(unittest.TestCase):
    def test_python_shell(self):
        """Test if PythonShell can be opened successfully.
        """
        self._devide_app._handlerMenuPythonShell(None)
        self.failUnless(self._devide_app._pythonShell._psFrame.IsShown())


class HelpContentsTest(unittest.TestCase):
    def test_help_contents(self):
        """Test if Help Contents can be opened successfully.
        """
        self._devide_app._handlerHelpContents(None)
        self.failUnless(
            self._devide_app._helpClass._htmlHelpController.GetFrame().\
            IsShown())

def get_suite(devide_app):
    basic_suite = unittest.TestSuite()
    
    t = PythonShellTest('test_python_shell')
    t._devide_app = devide_app
    basic_suite.addTest(t)

    t = HelpContentsTest('test_help_contents')
    t._devide_app = devide_app
    basic_suite.addTest(t)

    return basic_suite

    
    
