# testing.__init__.py copyright 2004 by Charl P. Botha http://cpbotha.net/
# $Id: __init__.py,v 1.3 2004/03/19 11:21:19 cpbotha Exp $
# this drives the devide unit testing.  neat huh?

import os
import unittest

_devideApp = None

# ----------------------------------------------------------------------------
class graphEditorTestBase(unittest.TestCase):
    def setUp(self):
        # make sure the graphEditor is running
        _devideApp._handlerMenuGraphEditor(None)
        # make sure we begin with a clean slate, so we can do
        # some module counting
        _devideApp._graphEditor.clearAllGlyphsFromCanvas()

class graphEditorVolumeTestBase(graphEditorTestBase):
    def setUp(self):
        # call parent setUp method
        graphEditorTestBase.setUp(self)

        # now let's build a volume we can play with
        # first the three modules
        (sqmod, sqglyph) = _devideApp._graphEditor.createModuleAndGlyph(
            10, 10, 'modules.Misc.superQuadric')

        (ivmod, ivglyph) = _devideApp._graphEditor.createModuleAndGlyph(
            10, 70, 'modules.Misc.implicitToVolume')

        (dtmod, dtglyph) = _devideApp._graphEditor.createModuleAndGlyph(
            10, 130, 'modules.Filters.doubleThreshold')

        # then configure the doubleThreshold with the correct thresholds
        cfg = dtmod.getConfig()
        cfg.lt = -99999.00
        cfg.ut = 0.0
        dtmod.setConfig(cfg)
        
        # now connect them all
        ret = _devideApp._graphEditor._connect(sqglyph, 0, ivglyph, 0)
        ret = _devideApp._graphEditor._connect(ivglyph, 0, dtglyph, 0)

        # redraw
        _devideApp._graphEditor._graphFrame.canvas.redraw()

        # run the network
        dtmod.executeModule()

        self.dtglyph = dtglyph
        self.dtmod = dtmod

        self.sqglyph = sqglyph
        self.sqmod = sqmod
        


# ----------------------------------------------------------------------------
class graphEditorBasic(graphEditorTestBase):
        
    def testStartup(self):
        """graphEditor startup.
        """
        self.failUnless(_devideApp._graphEditor._graphFrame.IsShown())

    def testModuleCreationDeletion(self):
        """Creation of simple module and glyph.
        """

        (mod, glyph) = _devideApp._graphEditor.createModuleAndGlyph(
            10, 10, 'modules.Misc.superQuadric')
        self.failUnless(mod and glyph)

        ret = _devideApp._graphEditor._deleteModule(glyph)
        self.failUnless(ret)

    def testSimpleNetwork(self):
        """Creation and connection of superQuadric source and slice3dVWR.
        """

        (sqmod, sqglyph) = _devideApp._graphEditor.createModuleAndGlyph(
            10, 10, 'modules.Misc.superQuadric')

        (svmod, svglyph) = _devideApp._graphEditor.createModuleAndGlyph(
            10, 70, 'modules.Viewers.slice3dVWR')

        ret = _devideApp._graphEditor._connect(sqglyph, 1, svglyph, 0)
        _devideApp._graphEditor._graphFrame.canvas.redraw()
        
        self.failUnless(ret)

class testReadersWriters(graphEditorVolumeTestBase):
    
    def testVTI(self):
        """Testing basic readers/writers.
        """
        self.failUnless(1 == 1)

# ----------------------------------------------------------------------------
class devideTesting:
    def __init__(self, devideApp):
        global _devideApp
        _devideApp = devideApp

        self.basicSuite = unittest.TestSuite()
        self.basicSuite.addTest(graphEditorBasic('testStartup'))
        self.basicSuite.addTest(graphEditorBasic('testModuleCreationDeletion'))
        self.basicSuite.addTest(graphEditorBasic('testSimpleNetwork'))
        self.basicSuite.addTest(testReadersWriters('testVTI'))

        self.mainSuite = unittest.TestSuite((self.basicSuite,))
        
        
    def runAllTests(self):
        runner = unittest.TextTestRunner()
        runner.run(self.mainSuite)

