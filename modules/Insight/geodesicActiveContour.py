# geodesicActiveContour.py
# $Id: geodesicActiveContour.py,v 1.9 2004/04/13 20:34:24 cpbotha Exp $

import fixitk as itk
import genUtils
from moduleBase import moduleBase
import moduleUtils
import moduleUtilsITK
from moduleMixins import scriptedConfigModuleMixin
import vtk
import ConnectVTKITKPython as CVIPy

class geodesicActiveContour(scriptedConfigModuleMixin, moduleBase):

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

    $Revision: 1.9 $
    """

    def __init__(self, moduleManager):

        moduleBase.__init__(self, moduleManager)
        
        # setup defaults
        self._config.propagationScaling = 2.0
        
        configList = [
            ('Propagation scaling:', 'propagationScaling', 'base:float',
             'text', 'Propagation scaling parameter for the geodesic active '
             'contour, '
             'i.e. balloon force.  Positive for outwards, negative for '
             'inwards.')]
        
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
            self._geodesicActiveContour.SetFeatureImage(inputStream)
            
        else:
            self._geodesicActiveContour.SetInput(inputStream)
            

    def getOutputDescriptions(self):
        return ('Image Data (ITK)',)

    def getOutput(self, idx):
        return self._thresholder.GetOutput()

    def configToLogic(self):
        self._geodesicActiveContour.SetPropagationScaling(
            self._config.propagationScaling)

    def logicToConfig(self):
        self._config.propagationScaling = self._geodesicActiveContour.\
                                          GetPropagationScaling()

    # --------------------------------------------------------------------
    # END OF API CALLS
    # --------------------------------------------------------------------

    def _createITKPipeline(self):
        # input: smoothing.SetInput()
        # output: thresholder.GetOutput()
        
        gAC = itk.itkGeodesicActiveContourLevelSetImageFilterF3F3_New()
        geodesicActiveContour = gAC
        geodesicActiveContour.SetCurvatureScaling( 1.0 );
        geodesicActiveContour.SetAdvectionScaling( 1.0 );
        geodesicActiveContour.SetMaximumRMSError( 0.02 );
        geodesicActiveContour.SetNumberOfIterations( 800 );
        #geodesicActiveContour.SetInput(  fastMarching.GetOutput() );
        #geodesicActiveContour.SetFeatureImage( sigmoid.GetOutput() );
        self._geodesicActiveContour = geodesicActiveContour
        moduleUtilsITK.setupITKObjectProgress(
            self, geodesicActiveContour,
            'GeodesicActiveContourLevelSetImageFilter',
            'Growing active contour')

        thresholder = itk.itkBinaryThresholdImageFilterF3US3_New()
        thresholder.SetLowerThreshold( -65535.0 );
        thresholder.SetUpperThreshold( 0.0 );
        thresholder.SetOutsideValue( 0  );
        thresholder.SetInsideValue( 65535 );
        thresholder.SetInput( geodesicActiveContour.GetOutput() );
        self._thresholder = thresholder
        moduleUtilsITK.setupITKObjectProgress(
            self, thresholder,
            'itkBinaryThresholdImageFilter',
            'Thresholding segmented areas')
        
    def _destroyITKPipeline(self):
        """Delete all bindings to components of the ITK pipeline.
        """

        del self._geodesicActiveContour
        del self._thresholder
        
