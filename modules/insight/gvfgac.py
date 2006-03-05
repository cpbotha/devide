# geodesicActiveContour.py
# $Id$

import itk
import module_kits.itk_kit as itk_kit
from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin

class gvfgac(scriptedConfigModuleMixin, moduleBase):

    """Module for performing Gradient Vector Flow-driven Geodesic Active
    Contour-based segmentation on 3D data.

    This module requires a DeVIDE-specific ITK class.

    The input feature image is an edge potential map with values close to 0 in
    regions close to the edges and values close to 1 otherwise.  The level set
    speed function is based on this.  For example: smooth an input image,
    determine the gradient magnitude and then pass it through a sigmoid
    transformation to create an edge potential map.

    The initial level set is a volume with the initial surface embedded as the
    0 level set, i.e. the 0-value iso-contour (more or less).  The inside of
    the volume is indicated by negative values and the outside with positive
    values.

    Also see figure 9.18 in the ITK Software Guide.

    $Revision: 1.2 $
    """

    def __init__(self, moduleManager):

        moduleBase.__init__(self, moduleManager)
        
        # setup defaults
        self._config.propagationScaling = 1.0
        self._config.curvatureScaling = 1.0
        self._config.advectionScaling = 1.0
        self._config.numberOfIterations = 100
        
        configList = [
            ('Propagation scaling:', 'propagationScaling', 'base:float',
             'text', 'Propagation scaling parameter for the geodesic active '
             'contour, '
             'i.e. balloon force.  Positive for outwards, negative for '
             'inwards.'),
            ('Curvature scaling:', 'curvatureScaling', 'base:float',
             'text', 'Curvature scaling term weighting.'),
            ('Advection scaling:', 'advectionScaling', 'base:float',
             'text', 'Advection scaling term weighting.'),
            ('Number of iterations:', 'numberOfIterations', 'base:int',
             'text',
             'Number of iterations that the algorithm should be run for')]
        
        scriptedConfigModuleMixin.__init__(self, configList)

        # call into scriptedConfigModuleMixin method
        self._createWindow({'Module (self)' : self})

        # create all pipeline thingies
        self._createITKPipeline()

        # send config down to logic and then all the way up to the view
        self.configToLogic()
        self.logicToConfig()
        self.configToView()

    def close(self):
        self._destroyITKPipeline()
        scriptedConfigModuleMixin.close(self)
        moduleBase.close(self)

    def executeModule(self):
        self.getOutput(0).Update()
        self._moduleManager.setProgress(
            100, "Geodesic active contour complete.")

    def getInputDescriptions(self):
        return ('Feature image (ITK)', 'Initial level set (ITK)' )

    def setInput(self, idx, inputStream):
        if idx == 0:
            self._gvfgac.SetFeatureImage(inputStream)
            
        else:
            self._gvfgac.SetInput(inputStream)
            

    def getOutputDescriptions(self):
        return ('Final level set (ITK Float 3D)',)

    def getOutput(self, idx):
        return self._gvfgac.GetOutput()

    def configToLogic(self):
        self._gvfgac.SetPropagationScaling(
            self._config.propagationScaling)

        self._gvfgac.SetCurvatureScaling(
            self._config.curvatureScaling)

        self._gvfgac.SetAdvectionScaling(
            self._config.advectionScaling)

        self._gvfgac.SetNumberOfIterations(
            self._config.numberOfIterations)

    def logicToConfig(self):
        self._config.propagationScaling = self._gvfgac.\
                                          GetPropagationScaling()

        self._config.curvatureScaling = self._gvfgac.\
                                        GetCurvatureScaling()

        self._config.advectionScaling = self._gvfgac.\
                                        GetAdvectionScaling()

        self._config.numberOfIterations = self._gvfgac.\
                                          GetNumberOfIterations()

    # --------------------------------------------------------------------
    # END OF API CALLS
    # --------------------------------------------------------------------

    def _createITKPipeline(self):
        # input: smoothing.SetInput()
        # output: thresholder.GetOutput()
        
        self._gvfgac = itk.itkGVFGACLevelSetImageFilterF3F3_New()
        #geodesicActiveContour.SetMaximumRMSError( 0.1 );

        itk_kit.utils.setupITKObjectProgress(
            self, self._gvfgac,
            'GVFGACLevelSetImageFilter',
            'Growing active contour')
        
    def _destroyITKPipeline(self):
        """Delete all bindings to components of the ITK pipeline.
        """

        del self._gvfgac
        
