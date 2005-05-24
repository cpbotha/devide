# testing.__init__.py copyright 2004 by Charl P. Botha http://cpbotha.net/
# $Id: __init__.py,v 1.8 2005/05/24 23:33:22 cpbotha Exp $
# this drives the devide unit testing.  neat huh?

import os
import unittest

_devideApp = None

# ----------------------------------------------------------------------------
class pythonShellTest(unittest.TestCase):
    def testPythonShell(self):
        """Test if PythonShell can be opened successfully.
        """
        _devideApp._handlerMenuPythonShell(None)
        self.failUnless(_devideApp._pythonShell._psFrame.IsShown())

# ----------------------------------------------------------------------------
class helpContentsTest(unittest.TestCase):
    def testHelpContents(self):
        """Test if Help Contents can be opened successfully.
        """
        _devideApp._handlerHelpContents(None)
        self.failUnless(
            _devideApp._helpClass._htmlHelpController.GetFrame().IsShown())


# ----------------------------------------------------------------------------
class graphEditorTestBase(unittest.TestCase):
    def setUp(self):
        # make sure the graphEditor is running
        _devideApp._handlerMenuGraphEditor(None)
        # make sure we begin with a clean slate, so we can do
        # some module counting
        _devideApp._graphEditor.clearAllGlyphsFromCanvas()

class graphEditorVolumeTestBase(graphEditorTestBase):
    """Uses superQuadric, implicitToVolume and doubleThreshold to create
    a volume that we can run some tests on.
    """
    
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

        # configure the implicitToVolume to have somewhat tighter bounds
        cfg = ivmod.getConfig()
        cfg.modelBounds = (-1.0, 1.0, -0.25, 0.25, 0.0, 0.75)
        ivmod.setConfig(cfg)

        # then configure the doubleThreshold with the correct thresholds
        cfg = dtmod.getConfig()
        cfg.lowerThreshold = -99999.00
        cfg.upperThreshold = 0.0
        dtmod.setConfig(cfg)
        
        # now connect them all
        ret = _devideApp._graphEditor._connect(sqglyph, 0, ivglyph, 0)
        ret = _devideApp._graphEditor._connect(ivglyph, 0, dtglyph, 0)

        # redraw
        _devideApp._graphEditor._canvasFrame.canvas.redraw()

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
        self.failUnless(
           _devideApp._graphEditor._canvasFrame.IsShown() and 
           _devideApp._graphEditor._modulePaletteFrame.IsShown())

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
        _devideApp._graphEditor._canvasFrame.canvas.redraw()
        
        self.failUnless(ret)

# ----------------------------------------------------------------------------
class testReadersWriters(graphEditorVolumeTestBase):
    
    def testVTI(self):
        """Testing basic readers/writers.
        """
        self.failUnless(1 == 1)

class testCoreModules(graphEditorTestBase):
    
    def testCreateDestroy(self):
        """See if we can create and destroy all core modules.
        """

        import modules
        reload(modules)

        coreModulesList = []
        for mn in modules.moduleList:
            if _devideApp.mainConfig.useInsight or \
               not mn.startswith('Insight'):
                coreModulesList.append('modules.%s' % (mn,))

        print coreModulesList

        self.failUnless(1 == 1)

# ----------------------------------------------------------------------------
class testITKBasic(graphEditorVolumeTestBase):

    def testConfidenceSeedConnect(self):
        """Test confidenceSeedConnect and VTK<->ITK interconnect.
        """

        # this will be the last big created thingy... from now on we'll
        # do DVNs.  This simulates the user's actions creating the network though.

        # create a slice3dVWR
        (svmod, svglyph) = _devideApp._graphEditor.createModuleAndGlyph(
            200, 190, 'modules.Viewers.slice3dVWR')

        # connect up the created volume and redraw
        ret = _devideApp._graphEditor._connect(self.dtglyph, 0, svglyph, 0)
        # make sure it can connect
        self.failUnless(ret)

        # storeCursor wants a 4-tuple and value - we know what these should be
        svmod.selectedPoints._storeCursor((20,20,0,1))

        # connect up the insight bits
        (v2imod, v2iglyph) = _devideApp._graphEditor.createModuleAndGlyph(
            200, 10, 'modules.Insight.VTKtoITKF3')

        (cscmod, cscglyph) = _devideApp._graphEditor.createModuleAndGlyph(
            200, 70, 'modules.Insight.confidenceSeedConnect')

        (i2vmod, i2vglyph) = _devideApp._graphEditor.createModuleAndGlyph(
            200, 130, 'modules.Insight.ITKF3toVTK')

        ret = _devideApp._graphEditor._connect(self.dtglyph, 0, v2iglyph, 0)
        self.failUnless(ret)
        
        ret = _devideApp._graphEditor._connect(v2iglyph, 0, cscglyph, 0)
        self.failUnless(ret)
        
        ret = _devideApp._graphEditor._connect(cscglyph, 0, i2vglyph, 0)
        self.failUnless(ret)

        # there's already something on the 0'th input of the slice3dVWR
        ret = _devideApp._graphEditor._connect(i2vglyph, 0, svglyph, 1)
        self.failUnless(ret)
        
        # connect up the selected points
        ret = _devideApp._graphEditor._connect(svglyph, 0, cscglyph, 1)
        self.failUnless(ret)        
        
        # redraw the canvas
        _devideApp._graphEditor._canvasFrame.canvas.redraw()

        

# ----------------------------------------------------------------------------
class devideTesting:
    def __init__(self, devideApp):
        global _devideApp
        _devideApp = devideApp

        self.basicSuite = unittest.TestSuite()
        self.basicSuite.addTest(pythonShellTest('testPythonShell'))
        self.basicSuite.addTest(helpContentsTest('testHelpContents'))
        self.basicSuite.addTest(graphEditorBasic('testStartup'))
        self.basicSuite.addTest(graphEditorBasic('testModuleCreationDeletion'))
        self.basicSuite.addTest(graphEditorBasic('testSimpleNetwork'))
        self.basicSuite.addTest(testReadersWriters('testVTI'))

        self.moduleSuite = unittest.TestSuite()
        self.moduleSuite.addTest(testCoreModules('testCreateDestroy'))

        self.itkSuite = unittest.TestSuite()
        self.itkSuite.addTest(testITKBasic('testConfidenceSeedConnect'))

        #suiteList = [self.basicSuite, self.moduleSuite]
        suiteList = [self.moduleSuite]

        if _devideApp.mainConfig.useInsight:
            suiteList.append(self.itkSuite)

        self.mainSuite = unittest.TestSuite(tuple(suiteList))
        
    def runAllTests(self):
        runner = unittest.TextTestRunner()
        runner.run(self.mainSuite)

