# geodesicActiveContour.py
# $Id: geodesicActiveContour.py,v 1.8 2004/04/13 17:03:03 cpbotha Exp $

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

    We make use of the following pipelines:<br>
    1. reader -> smoothing -> gradientMagnitude -> sigmoid -> FI<br>
    2. fastMarching -> geodesicActiveContour(FI) -> thresholder -> writer<br>
    The output of pipeline 1 is a feature image that is used by the
    geodesicActiveContour object.  Also see figure 9.18 in the ITK
    Software Guide.

    $Revision: 1.8 $
    """

    def __init__(self, moduleManager):

        moduleBase.__init__(self, moduleManager)
        
        # setup defaults
        self._config.sigma = 1.0
        self._config.sigmoidAlpha = -0.5
        self._config.sigmoidBeta = 3.0
        self._config.propagationScaling = 2.0
        
        configList = [
            ('Sigma:', 'sigma', 'base:float', 'text',
             'Sigma parameter of the Gaussian that will be used to calculate '
             'the gradient.'),
            ('Sigmoid Alpha:', 'sigmoidAlpha', 'base:float', 'text',
             'Alpha parameter for the sigmoid filter'),
            ('Sigmoid Beta:', 'sigmoidBeta', 'base:float', 'text',
             'Beta parameter for the sigmoid filter'),
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
        return ('Input Image (ITK)', 'Initial level set (ITK)' )

    def setInput(self, idx, inputStream):
        if idx == 0:
            self._smoothing.SetInput(inputStream)
            
        else:
            self._geodesicActiveContour.SetInput(inputStream)
            

    def getOutputDescriptions(self):
        return ('Image Data (ITK)',)

    def getOutput(self, idx):
        return self._thresholder.GetOutput()

    def configToLogic(self):
        self._gradientMagnitude.SetSigma(self._config.sigma)

        self._sigmoid.SetAlpha(self._config.sigmoidAlpha)
        self._sigmoid.SetBeta(self._config.sigmoidBeta)
        
        self._geodesicActiveContour.SetPropagationScaling(
            self._config.propagationScaling)

    def logicToConfig(self):
        # we can't get sigma (no getter)

        # these two aren't wrapped for some or other reason?
        #self._config.sigmoidAlpha = self._sigmoid.GetAlpha()
        #self._config.sigmoidBeta = self._sigmoid.GetBeta()

        self._config.propagationScaling = self._geodesicActiveContour.\
                                          GetPropagationScaling()

    # --------------------------------------------------------------------
    # END OF API CALLS
    # --------------------------------------------------------------------

    def _createITKPipeline(self):
        # input: smoothing.SetInput()
        # output: thresholder.GetOutput()
        
        # ITK 1: smoothing -> gradientMagnitude -> sigmoid -> FI
        smoothing = itk.itkCurvatureAnisotropicDiffusionImageFilterF3F3_New()
        smoothing.SetTimeStep( 0.0625 );
        smoothing.SetNumberOfIterations(  5 );
        smoothing.SetConductanceParameter( 3.0 );
        self._smoothing = smoothing
        moduleUtilsITK.setupITKObjectProgress(
            self, smoothing, 'itkCurvatureAnisotropicDiffusionImageFilter',
            'Smoothing data')

        gM = itk.itkGradientMagnitudeRecursiveGaussianImageFilterF3F3_New()
        gradientMagnitude = gM
        gradientMagnitude.SetInput( smoothing.GetOutput() );
        self._gradientMagnitude = gradientMagnitude
        moduleUtilsITK.setupITKObjectProgress(
            self, gradientMagnitude,
            'itkGradientMagnitudeRecursiveGaussianImageFilter',
            'Calculating gradient magnitude')

        sigmoid = itk.itkSigmoidImageFilterF3F3_New()
        sigmoid.SetOutputMinimum(  0.0  );
        sigmoid.SetOutputMaximum(  1.0  );
        sigmoid.SetInput( gradientMagnitude.GetOutput() );
        self._sigmoid = sigmoid
        moduleUtilsITK.setupITKObjectProgress(
            self, sigmoid,
            'itkSigmoidImageFilter', 'Calculating feature image with sigmoid')

        # ITK 2: fastMarching -> geodesicActiveContour(FI) -> thresholder

        gAC = itk.itkGeodesicActiveContourLevelSetImageFilterF3F3_New()
        geodesicActiveContour = gAC
        geodesicActiveContour.SetCurvatureScaling( 1.0 );
        geodesicActiveContour.SetAdvectionScaling( 1.0 );
        geodesicActiveContour.SetMaximumRMSError( 0.02 );
        geodesicActiveContour.SetNumberOfIterations( 800 );
        #geodesicActiveContour.SetInput(  fastMarching.GetOutput() );
        geodesicActiveContour.SetFeatureImage( sigmoid.GetOutput() );
        self._geodesicActiveContour = geodesicActiveContour
        moduleUtilsITK.setupITKObjectProgress(
            self, geodesicActiveContour,
            'GeodesicActiveContourLevelSetImageFilter',
            'Growing active contour')

        thresholder = itk.itkBinaryThresholdImageFilterF3US3_New()
        thresholder.SetLowerThreshold( -1000.0 );
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

        del self._smoothing
        del self._gradientMagnitude
        del self._sigmoid
        del self._geodesicActiveContour
        del self._thresholder
        
