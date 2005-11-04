# $Id: symmetricDemonsRegistration.py,v 1.3 2005/11/04 10:34:55 cpbotha Exp $

import fixitk as itk
from moduleBase import moduleBase
import moduleUtils
import moduleUtilsITK
from moduleMixins import scriptedConfigModuleMixin

class symmetricDemonsRegistration(scriptedConfigModuleMixin, moduleBase):
    """Performs symmetric forces demons registration on fixed and moving input
    images, returns deformation field.

    $Revision: 1.3 $
    """
    
    def __init__(self, moduleManager):
        
        moduleBase.__init__(self, moduleManager)

        self._config.numberOfIterations = 50
        self._config.deformationSmoothingStd = 1.0
        self._config.idiffThresh = 0.001

        configList = [
            ('Number of iterations:', 'numberOfIterations',
             'base:int', 'text',
             'Number of iterations for the Demons registration to run.'),
            ('Standard deviation of vector smoothing:',
             'deformationSmoothingStd', 'base:float', 'text',
             'Standard deviation of Gaussian kernel used to smooth '
             'intermediate deformation field'),            
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

        self._demons = itk.itkSymmetricForcesDemonsRegistrationFilterF3F3_New()
        self._demons.SetStandardDeviations(1.0)
        self._demons.SetMovingImage(self._matcher.GetOutput())

        moduleUtilsITK.setupITKObjectProgress(
            self, self._demons, 'itkSymmetricForcesDemonsRegistration',
            'Performing registration, metric = %.2f', ('GetMetric()',))

        self._createWindow(
            {'Module (self)' : self,
             'itkSymmetricForcesDemonsRegistrationFilter' : self._demons,
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
        del self._demons
        del self._matcher

    def executeModule(self):
        self.getOutput(0).Update()

    def getInputDescriptions(self):
        return ('Fixed image (ITK 3D Float)', 'Moving image (ITK 3D Float)')

    def setInput(self, idx, inputStream):
        if idx == 0:
            self._matcher.SetReferenceImage(inputStream)
            self._demons.SetFixedImage(inputStream)

        else:
            self._matcher.SetInput(inputStream)
        
    def getOutputDescriptions(self):
        return ('Deformation field (ITK 3D Float vectors)',)

    def getOutput(self, idx):
        return self._demons.GetOutput()

    def configToLogic(self):
        self._demons.SetNumberOfIterations(self._config.numberOfIterations)
        self._demons.SetStandardDeviations(
            self._config.deformationSmoothingStd)
        self._demons.SetIntensityDifferenceThreshold(
            self._config.idiffThresh)

    def logicToConfig(self):
        self._config.numberOfIterations = self._demons.GetNumberOfIterations()
        # we can't get the StandardDeviations back...
        self._config.idiffThresh = \
                                 self._demons.GetIntensityDifferenceThreshold()
        

    
        
