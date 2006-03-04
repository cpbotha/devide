"""Module to test graph_editor functionality.
"""

import os
import time
import unittest

class GraphEditorTestBase(unittest.TestCase):
    def setUp(self):
        # make sure the graphEditor is running
        self._devide_app._handlerMenuGraphEditor(None)
        # make sure we begin with a clean slate, so we can do
        # some module counting
        self._devide_app._graphEditor.clearAllGlyphsFromCanvas()

class GraphEditorVolumeTestBase(GraphEditorTestBase):
    """Uses superQuadric, implicitToVolume and doubleThreshold to create
    a volume that we can run some tests on.
    """
    
    def setUp(self):
        # call parent setUp method
        GraphEditorTestBase.setUp(self)

        # now let's build a volume we can play with
        # first the three modules
        (sqmod, sqglyph) = self._devide_app._graphEditor.createModuleAndGlyph(
            10, 10, 'modules.Misc.superQuadric')

        (ivmod, ivglyph) = self._devide_app._graphEditor.createModuleAndGlyph(
            10, 70, 'modules.Misc.implicitToVolume')

        (dtmod, dtglyph) = self._devide_app._graphEditor.createModuleAndGlyph(
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
        ret = self._devide_app._graphEditor._connect(sqglyph, 0, ivglyph, 0)
        ret = self._devide_app._graphEditor._connect(ivglyph, 0, dtglyph, 0)

        # redraw
        self._devide_app._graphEditor._graphEditorFrame.canvas.redraw()

        # run the network
        dtmod.executeModule()

        self.dtglyph = dtglyph
        self.dtmod = dtmod

        self.sqglyph = sqglyph
        self.sqmod = sqmod
        


# ----------------------------------------------------------------------------
class GraphEditorBasic(GraphEditorTestBase):
        
    def test_startup(self):
        """graphEditor startup.
        """
        self.failUnless(
           self._devide_app._graphEditor._graphEditorFrame.IsShown())

    def test_module_creation_deletion(self):
        """Creation of simple module and glyph.
        """

        (mod, glyph) = self._devide_app._graphEditor.createModuleAndGlyph(
            10, 10, 'modules.misc.superQuadric')
        self.failUnless(mod and glyph)

        ret = self._devide_app._graphEditor._deleteModule(glyph)
        self.failUnless(ret)

    def testModuleHelp(self):
        """See if module specific help can be called up for a module.
        """

        (mod, glyph) = self._devide_app._graphEditor.createModuleAndGlyph(
            10, 10, 'modules.Writers.vtiWRT')
        self.failUnless(mod and glyph)

        self._devide_app._graphEditor._helpModule(mod)

        # find frame that should have appeared by now
        fullModuleName = mod.__class__.__module__
        htmlWindowFrame = self._devide_app._graphEditor._moduleHelpFrames[
            fullModuleName]

        # fail if it's not there
        self.failUnless(htmlWindowFrame.IsShown())

        # take it away
        ret = self._devide_app._graphEditor._deleteModule(glyph)
        self.failUnless(ret)

    def testSimpleNetwork(self):
        """Creation and connection of superQuadric source and slice3dVWR.
        """

        (sqmod, sqglyph) = self._devide_app._graphEditor.createModuleAndGlyph(
            10, 10, 'modules.Misc.superQuadric')

        (svmod, svglyph) = self._devide_app._graphEditor.createModuleAndGlyph(
            10, 90, 'modules.Viewers.slice3dVWR')

        ret = self._devide_app._graphEditor._connect(sqglyph, 1, svglyph, 0)
        self._devide_app._graphEditor._graphEditorFrame.canvas.redraw()
        
        self.failUnless(ret)

    def testConfigVtkObj(self):
        """See if the ConfigVtkObj is available and working.
        """

        # first create superQuadric
        (sqmod, sqglyph) = self._devide_app._graphEditor.createModuleAndGlyph(
            10, 10, 'modules.Misc.superQuadric')

        self.failUnless(sqmod and sqglyph)

        self._devide_app._graphEditor._viewConfModule(sqmod)

        # superQuadric is a standard scriptedConfigModuleMixin, so it has
        # a _viewFrame ivar
        self.failUnless(sqmod._viewFrame.IsShown())

        # start up the vtkObjectConfigure window for that object
        sqmod.vtkObjectConfigure(sqmod._viewFrame, None, sqmod._superquadric)

        # check that it's visible
        # sqmod._vtk_obj_cfs[sqmod._superquadric] is the ConfigVtkObj instance
        self.failUnless(
            sqmod._vtk_obj_cfs[sqmod._superquadric]._frame.IsShown())

        # end by closing them all (so now all we're left with is the
        # module view itself)
        sqmod.closeVtkObjectConfigure()

        # remove the module as well
        ret = self._devide_app._graphEditor._deleteModule(sqglyph)
        self.failUnless(ret)
        


# ----------------------------------------------------------------------------
class TestReadersWriters(GraphEditorVolumeTestBase):
    
    def testVTI(self):
        """Testing basic readers/writers.
        """
        self.failUnless(1 == 1)

class TestModulesMisc(GraphEditorTestBase):
    
    def testCreateDestroy(self):
        """See if we can create and destroy all core modules.
        """

        import modules
        reload(modules)

        modulesList = []

        mm = self._devide_app.get_module_manager()

        for module_name in mm.getAvailableModules().keys():
            print 'About to create %s.' % (module_name,)
            
            (cmod, cglyph) = self._devide_app._graphEditor.createModuleAndGlyph(
                10, 10, module_name)

            print 'Created %s.' % (module_name,)
            self.failUnless(cmod and cglyph)

            # destroy
            ret = self._devide_app._graphEditor._deleteModule(cglyph)
            print 'Destroyed %s.' % (module_name,)
            self.failUnless(ret)


        self.failUnless(1 == 1)

# ----------------------------------------------------------------------------
class TestITKBasic(GraphEditorVolumeTestBase):

    def testConfidenceSeedConnect(self):
        """Test confidenceSeedConnect and VTK<->ITK interconnect.
        """

        # this will be the last big created thingy... from now on we'll
        # do DVNs.  This simulates the user's actions creating the network
        # though.

        # create a slice3dVWR
        (svmod, svglyph) = self._devide_app._graphEditor.createModuleAndGlyph(
            200, 190, 'modules.Viewers.slice3dVWR')

        # connect up the created volume and redraw
        ret = self._devide_app._graphEditor._connect(self.dtglyph, 0, svglyph, 0)
        # make sure it can connect
        self.failUnless(ret)

        # storeCursor wants a 4-tuple and value - we know what these should be
        svmod.selectedPoints._storeCursor((20,20,0,1))

        # connect up the insight bits
        (v2imod, v2iglyph) = self._devide_app._graphEditor.createModuleAndGlyph(
            200, 10, 'modules.Insight.VTKtoITKF3')

        (cscmod, cscglyph) = self._devide_app._graphEditor.createModuleAndGlyph(
            200, 70, 'modules.Insight.confidenceSeedConnect')

        (i2vmod, i2vglyph) = self._devide_app._graphEditor.createModuleAndGlyph(
            200, 130, 'modules.Insight.ITKF3toVTK')

        ret = self._devide_app._graphEditor._connect(self.dtglyph, 0, v2iglyph, 0)
        self.failUnless(ret)
        
        ret = self._devide_app._graphEditor._connect(v2iglyph, 0, cscglyph, 0)
        self.failUnless(ret)
        
        ret = self._devide_app._graphEditor._connect(cscglyph, 0, i2vglyph, 0)
        self.failUnless(ret)

        # there's already something on the 0'th input of the slice3dVWR
        ret = self._devide_app._graphEditor._connect(i2vglyph, 0, svglyph, 1)
        self.failUnless(ret)
        
        # connect up the selected points
        ret = self._devide_app._graphEditor._connect(svglyph, 0, cscglyph, 1)
        self.failUnless(ret)        
        
        # redraw the canvas
        self._devide_app._graphEditor._graphEditorFrame.canvas.redraw()

def create_geb_test(name, devide_app):
    """Utility function to create GraphEditorBasic test and stuff all the
    data in there that we'd like.
    """
    
    t = GraphEditorBasic(name)
    t._devide_app = devide_app
    return t

def get_suite(devide_app):
    graph_editor_suite = unittest.TestSuite()

    graph_editor_suite.addTest(create_geb_test('test_startup', devide_app))
    graph_editor_suite.addTest(
        create_geb_test('test_module_creation_deletion', devide_app))
    

    return graph_editor_suite
