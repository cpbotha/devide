# geodesicActiveContour.py
# $Id: geodesicActiveContour.py,v 1.7 2004/03/03 11:26:25 cpbotha Exp $

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

    $Revision: 1.7 $
    """

    def __init__(self, moduleManager):

        moduleBase.__init__(self, moduleManager)
        
        # setup defaults
        self._config.initialDistance = 5.0
        self._config.sigma = 1.0
        self._config.sigmoidAlpha = -0.5
        self._config.sigmoidBeta = 3.0
        self._config.propagationScaling = 2.0
        
        configList = [
            ('Initial Distance:', 'initialDistance', 'base:float', 'text',
             'The initial distance of the initial front.'),
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
        self._createConnectPipeline()

        # send config down to logic and then all the way up to the view
        self.configToLogic()
        self.syncViewWithLogic()

    def close(self):
        self._destroyConnectPipeline()
        self._destroyITKPipeline()
        scriptedConfigModuleMixin.close(self)
        moduleBase.close(self)

    def executeModule(self):
        self.getOutput(0).Update()

    def getInputDescriptions(self):
        return ('Image Data', )

    def setInput(self, idx, inputStream):
        self._inputImageCast.SetInput(inputStream)
        if inputStream != None:
            inputStream.Update()
            dims = inputStream.GetDimensions()
            print dims
            sz = itk.itkSize3()
            sz.SetElement(0, dims[0])
            sz.SetElement(1, dims[1])
            sz.SetElement(2, dims[2])            
            
            self._fastMarching.SetOutputSize(sz)

    def getOutputDescriptions(self):
        return ('Image Data',)

    def getOutput(self, idx):
        #return self._pSource.GetStructuredPointsOutput()
        return self._vtkImporter.GetOutput()

    def configToLogic(self):
        self._gradientMagnitude.SetSigma(self._config.sigma)

        self._sigmoid.SetAlpha(self._config.sigmoidAlpha)
        self._sigmoid.SetBeta(self._config.sigmoidBeta)
        
        # FIXME: make sure points are here
        seedPosition = itk.itkIndex3()
        # test position with r256 (this could take a while)
        seedPosition.SetElement(0, 19)
        seedPosition.SetElement(1, 25)
        seedPosition.SetElement(2, 43)        

        seedValue = - self._config.initialDistance
        node = itk.itkLevelSetNodeF3()
        node.SetValue(seedValue)
        node.SetIndex(seedPosition)

        seeds = itk.itkNodeContainerF3_New()
        seeds.Initialize()
        seeds.InsertElement(0, node)

        self._fastMarching.SetTrialPoints(seeds.GetPointer())

        self._geodesicActiveContour.SetPropagationScaling(
            self._config.propagationScaling)

    def logicToConfig(self):
        # we can't get sigma (no getter)
        # we can't get initialDistance (meta)

        # these two aren't wrapped for some or other reason?
        #self._config.sigmoidAlpha = self._sigmoid.GetAlpha()
        #self._config.sigmoidBeta = self._sigmoid.GetBeta()

        self._config.propagationScaling = self._geodesicActiveContour.\
                                          GetPropagationScaling()

    # --------------------------------------------------------------------
    # END OF API CALLS
    # --------------------------------------------------------------------

    def _createITKPipeline(self):
        # FIXME: remove this
        reload(moduleUtilsITK)
        
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
        fastMarching = itk.itkFastMarchingImageFilterF3F3_New()
        fastMarching.SetSpeedConstant(1.0)
        self._fastMarching = fastMarching
        moduleUtilsITK.setupITKObjectProgress(
            self, fastMarching,
            'itkFastMarchingImageFilter', 'Calculating initial distance field')

        gAC = itk.itkGeodesicActiveContourLevelSetImageFilterF3F3_New()
        geodesicActiveContour = gAC
        geodesicActiveContour.SetCurvatureScaling( 1.0 );
        geodesicActiveContour.SetAdvectionScaling( 1.0 );
        geodesicActiveContour.SetMaximumRMSError( 0.02 );
        geodesicActiveContour.SetNumberOfIterations( 800 );
        geodesicActiveContour.SetInput(  fastMarching.GetOutput() );
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


    def _createConnectPipeline(self):
        """When creating a new VTK->ITK-VTK pipeline, copy this method,
        as well as _psExecute.
        """
        
        # this is the main module input
        self._inputImageCast = vtk.vtkImageCast()
        self._inputImageCast.SetOutputScalarTypeToFloat()

        self._vtkExporter = vtk.vtkImageExport()
        self._vtkExporter.SetInput(self._inputImageCast.GetOutput())

        self._itkImporter = itk.itkVTKImageImportF3_New()
        CVIPy.ConnectVTKToITKF3(
            self._vtkExporter, self._itkImporter.GetPointer())

        # make the connection with the input object in the ITK pipeline
        self._smoothing.SetInput(self._itkImporter.GetOutput())

        # make the connection with the output object in the ITK pipeline
        self._itkExporter = itk.itkVTKImageExportUS3_New()
        self._itkExporter.SetInput(self._thresholder.GetOutput())

        self._vtkImporter = vtk.vtkImageImport()
        CVIPy.ConnectITKUS3ToVTK(
            self._itkExporter.GetPointer(), self._vtkImporter)


    def _destroyConnectPipeline(self):
        del self._inputImageCast
        del self._vtkExporter
        del self._itkImporter
        del self._itkExporter
        del self._vtkImporter
        
    def _destroyITKPipeline(self):
        """Delete all bindings to components of the ITK pipeline.
        """

        del self._smoothing
        del self._gradientMagnitude
        del self._sigmoid
        del self._fastMarching
        del self._geodesicActiveContour
        del self._thresholder
        
