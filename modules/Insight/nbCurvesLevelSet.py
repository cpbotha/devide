# geodesicActiveContour.py
# $Id: nbCurvesLevelSet.py,v 1.1 2004/04/15 12:51:22 cpbotha Exp $

import fixitk as itk
import genUtils
from moduleBase import moduleBase
import moduleUtils
import moduleUtilsITK
from moduleMixins import scriptedConfigModuleMixin
import vtk
import ConnectVTKITKPython as CVIPy

class nbCurvesLevelSet(scriptedConfigModuleMixin, moduleBase):

    """Module for performing Geodesic Active Contour-based segmentation on
    3D data.

    The input feature image is an edge potential map with values close to 0 in
    regions close to the edges and values close to 1 otherwise.  The level set
    speed function is based on this.  For example: smooth an input image,
    determine the gradient magnitude and then pass it through a sigmoid
    transformation to create an edge potential map.

    The initial level set is a volume with the initial surface embedded as the
    0 level set, i.e. the 0-value iso-contour (more or less).

    Also see figure 9.18 in the ITK Software Guide.

    $Revision: 1.1 $
    """

    def __init__(self, moduleManager):

        moduleBase.__init__(self, moduleManager)
        
        # setup defaults
        self._config.propagationScaling = 1.0
        self._config.advectionScaling = 1.0
        self._config.curvatureScaling = 1.0
        
        configList = [
            ('Propagation scaling:', 'propagationScaling', 'base:float',
             'text', 'Weight factor for the propagation term'),
            ('Advection scaling:', 'advectionScaling', 'base:float',
             'text', 'Weight factor for the advection term'),
            ('Curvature scaling:', 'curvatureScaling', 'base:float',
             'text', 'Weight factor for the curvature term')]
        
        scriptedConfigModuleMixin.__init__(self, configList)

        # call into scriptedConfigModuleMixin method
        self._createWindow({'Module (self)' : self})

        # create all pipeline thingies
        self._createITKPipeline()

        # send config down to logic and then all the way up to the view
        self.configToLogic()
        self.syncViewWithLogic()

    def close(self):
        self._destroyITKPipeline()
        scriptedConfigModuleMixin.close(self)
        moduleBase.close(self)

    def executeModule(self):
        self.getOutput(0).Update()

    def getInputDescriptions(self):
        return ('Feature image (ITK)', 'Initial level set (ITK)' )

    def setInput(self, idx, inputStream):
        if idx == 0:
            self._nbcLS.SetFeatureImage(inputStream)
            
        else:
            self._nbcLS.SetInput(inputStream)
            

    def getOutputDescriptions(self):
        return ('Image Data (ITK)',)

    def getOutput(self, idx):
        return self._thresholder.GetOutput()

    def configToLogic(self):
        self._nbcLS.SetPropagationScaling(
            self._config.propagationScaling)

        self._nbcLS.SetAdvectionScaling(
            self._config.advectionScaling)

        self._nbcLS.SetCurvatureScaling(
            self._config.curvatureScaling)

    def logicToConfig(self):
        self._config.propagationScaling = self._nbcLS.\
                                          GetPropagationScaling()

        self._config.advectionScaling = self._nbcLS.GetAdvectionScaling()

        self._config.curvatureScaling = self._nbcLS.GetCurvatureScaling()

    # --------------------------------------------------------------------
    # END OF API CALLS
    # --------------------------------------------------------------------

    def _createITKPipeline(self):
        # input: smoothing.SetInput()
        # output: thresholder.GetOutput()

        self._nbcLS = itk.itkNarrowBandCurvesLevelSetImageFilterF3F3_New()
        self._nbcLS.SetMaximumRMSError( 0.1 );
        self._nbcLS.SetNumberOfIterations( 500 );

        moduleUtilsITK.setupITKObjectProgress(
            self, self._nbcLS,
            'NarrowBandCurvesLevelSetImageFilter',
            'Evolving level set')

        thresholder = itk.itkBinaryThresholdImageFilterF3US3_New()
        thresholder.SetLowerThreshold( -65535.0 );
        thresholder.SetUpperThreshold( 0.0 );
        thresholder.SetOutsideValue( 0  );
        thresholder.SetInsideValue( 65535 );
        thresholder.SetInput(self._nbcLS.GetOutput() );
        self._thresholder = thresholder
        moduleUtilsITK.setupITKObjectProgress(
            self, thresholder,
            'itkBinaryThresholdImageFilter',
            'Thresholding segmented areas')
        
    def _destroyITKPipeline(self):
        """Delete all bindings to components of the ITK pipeline.
        """

        del self._nbcLS
        del self._thresholder
        
