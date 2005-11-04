# $Id: levelSetMotionRegistration.py,v 1.4 2005/11/04 10:34:55 cpbotha Exp $

import fixitk as itk
from moduleBase import moduleBase
import moduleUtils
import moduleUtilsITK
from moduleMixins import scriptedConfigModuleMixin

class levelSetMotionRegistration(scriptedConfigModuleMixin, moduleBase):
    """Performs deformable registration between two input volumes using
    level set motion.

    $Revision: 1.4 $
    """
    
    def __init__(self, moduleManager):
        
        moduleBase.__init__(self, moduleManager)

        self._config.numberOfIterations = 50
        self._config.gradSmoothStd = 1.0
        self._config.alpha = 0.1
        self._config.idiffThresh = 0.001

        configList = [
            ('Number of iterations:', 'numberOfIterations',
             'base:int', 'text',
             'Number of iterations for the Demons registration to run.'),
            ('Gradient smoothing standard deviation:', 'gradSmoothStd',
             'base:float', 'text',
             'The standard deviation of the Gaussian kernel in physical '
             'units that will be '
             'used to smooth the images before calculating gradients.'),
            ('Stability parameter alpha:', 'alpha', 'base:float', 'text',
             'Used to stabilise small gradient magnitude values.  Set to '
             'approximately 0.04% of intensity range of input images.'),
            ('Intensity difference threshold:', 'idiffThresh',
             'base:float', 'text',
             'Voxels differing with less than this threshold are considered '
             'equal')]

        scriptedConfigModuleMixin.__init__(self, configList)

        # input 1 is fixed, input 2 is moving
        # matcher.SetInput(moving)
        # matcher.SetReferenceImage(fixed)
        
        self._matcher = itk.itkHistogramMatchingImageFilterF3F3_New()
        self._matcher.SetNumberOfHistogramLevels(1024)
        self._matcher.SetNumberOfMatchPoints(7)
        self._matcher.ThresholdAtMeanIntensityOn()

        self._levelSetMotion = \
                             itk.itkLevelSetMotionRegistrationFilterF3F3_New()
        self._levelSetMotion.SetMovingImage(self._matcher.GetOutput())

        # we should get a hold of GetElapsedIterations...
        # DenseFiniteDifference -> PDEDeformableRegistration -> LevelSetMotion
        # Dense still has it, PDE onwards doesn't.  Dense is templated on
        # input and output, PDE on two image types and a deformation field...
        moduleUtilsITK.setupITKObjectProgress(
            self, self._levelSetMotion, 'itkLevelSetMotionRegistrationFilter',
            'Performing registration, metric = %.2f',
            ('GetMetric()',))

        self._createWindow(
            {'Module (self)' : self,
             'itkLevelSetMotionRegistrationFilter' : self._levelSetMotion,
             'itkHistogramMatchingImageFilter' : self._matcher})

        self.configToLogic()
        self.logicToConfig()
        self.configToView()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)
        # and the baseclass close
        moduleBase.close(self)
            
        # remove all bindings
        del self._levelSetMotion
        del self._matcher

    def executeModule(self):
        self.getOutput(0).Update()

    def getInputDescriptions(self):
        return ('Fixed image (ITK 3D Float)', 'Moving image (ITK 3D Float)')

    def setInput(self, idx, inputStream):
        if idx == 0:
            self._matcher.SetReferenceImage(inputStream)
            self._levelSetMotion.SetFixedImage(inputStream)

        else:
            self._matcher.SetInput(inputStream)
        
    def getOutputDescriptions(self):
        return ('Deformation field (ITK 3D Float vectors)',)

    def getOutput(self, idx):
        return self._levelSetMotion.GetOutput()

    def configToLogic(self):
        self._levelSetMotion.SetNumberOfIterations(
            self._config.numberOfIterations)
        self._levelSetMotion.SetGradientSmoothingStandardDeviations(
            self._config.gradSmoothStd)
        self._levelSetMotion.SetAlpha(self._config.alpha)
        self._levelSetMotion.SetIntensityDifferenceThreshold(
            self._config.idiffThresh)

    def logicToConfig(self):
        self._config.numberOfIterations = self._levelSetMotion.\
                                          GetNumberOfIterations()
        
        self._config.gradSmoothStd = \
                                   self._levelSetMotion.\
                                   GetGradientSmoothingStandardDeviations()

        self._config.alpha = \
                           self._levelSetMotion.GetAlpha()
        
        self._config.idiffThresh = \
                                 self._levelSetMotion.\
                                 GetIntensityDifferenceThreshold()
        

    
        
