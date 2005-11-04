# $Id: curvatureFlowDenoising.py,v 1.2 2005/11/04 10:34:55 cpbotha Exp $

import fixitk as itk
import genUtils
from moduleBase import moduleBase
import moduleUtils
import moduleUtilsITK
from moduleMixins import scriptedConfigModuleMixin

class curvatureFlowDenoising(scriptedConfigModuleMixin, moduleBase):
    """Curvature-driven image denoising.

    This uses curvature-based level set techniques to smooth
    homogeneous regions whilst retaining boundary information.
    
    $Revision: 1.2 $
    """
    
    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        self._config.numberOfIterations = 3
        self._config.timeStep = 0.05

        configList = [
            ('Number of iterations:', 'numberOfIterations', 'base:int',
             'text',
             'Number of update iterations that will be performed.'),

            ('Timestep:', 'timeStep', 'base:float',
             'text', 'Timestep between update iterations.')]

        
        scriptedConfigModuleMixin.__init__(self, configList)


        # setup the pipeline
        self._cfif = itk.itkCurvatureFlowImageFilterF3F3_New()
        
        moduleUtilsITK.setupITKObjectProgress(
            self, self._cfif, 'itkCurvatureFlowImageFilter',
            'Denoising data')

        self._createWindow(
            {'Module (self)' : self,
             'itkCurvatureFlowImageFilter' : self._cfif})

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
        del self._cfif

    def executeModule(self):
        self._cfif.Update()
        self._moduleManager.setProgress(100, "Denoising data [DONE]")

    def getInputDescriptions(self):
        return ('ITK Image (3D, float)',)

    def setInput(self, idx, inputStream):
        self._cfif.SetInput(inputStream)

    def getOutputDescriptions(self):
        return ('Denoised ITK Image (3D, float)',)

    def getOutput(self, idx):
        return self._cfif.GetOutput()

    def configToLogic(self):
        self._cfif.SetNumberOfIterations(self._config.numberOfIterations)
        self._cfif.SetTimeStep(self._config.timeStep)

    def logicToConfig(self):
        self._config.numberOfIterations = self._cfif.GetNumberOfIterations()
        self._config.timeStep = self._cfif.GetTimeStep()
        
                                          
