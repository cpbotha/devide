# testing.__init__.py copyright 2004 by Charl P. Botha http://cpbotha.net/
# $Id: __init__.py,v 1.1 2004/03/17 20:57:13 cpbotha Exp $
# this drives the devide unit testing.  neat huh?

import unittest

_devideApp = None

class graphEditorBasic(unittest.TestCase):

    def setUp(self):
        # make sure the graphEditor is running
        _devideApp._handlerMenuGraphEditor(None)
        # make sure we begin with a clean slate, so we can do
        # some module counting
        _devideApp.clearAllGlyphsFromCanvas()
        
    def testStartup(self):
        """graphEditor startup.
        """
        self.failUnless(_devideApp._graphEditor._graphFrame.IsShown())

    def testModuleCreation(self):
        """Creation of simple module and glyph.
        """

        _devideApp._graphEditor.createModuleAndGlyph(
            10, 10, 'modules.Misc.superQuadric')

class devideTesting:
    def __init__(self, devideApp):
        global _devideApp
        _devideApp = devideApp
        
    def runAllTests(self):
        basicSuite = unittest.TestSuite()
        basicSuite.addTest(graphEditorBasic('testStartup'))
        basicSuite.addTest(graphEditorBasic('testModuleCreation'))        

        mainTestSuite = unittest.TestSuite((basicSuite,))

        runner = unittest.TextTestRunner()
        runner.run(mainTestSuite)

