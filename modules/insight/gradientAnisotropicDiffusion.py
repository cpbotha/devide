# $Id$

import itk
from moduleBase import moduleBase
import module_kits.itk_kit
from moduleMixins import scriptedConfigModuleMixin

class gradientAnisotropicDiffusion(scriptedConfigModuleMixin, moduleBase):
    """Performs a gradient-based anisotropic diffusion.

    This will smooth homogeneous areas whilst preserving features
    (e.g. edges).

    $Revision: 1.4 $
    """
    
    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        self._config.numberOfIterations = 5
        self._config.conductanceParameter = 3.0

        configList = [
            ('Number of iterations:', 'numberOfIterations', 'base:int', 'text',
             'Number of time-step updates (iterations) the solver will '
             'perform.'),
            ('Conductance parameter:', 'conductanceParameter', 'base:float',
             'text', 'Sensitivity of the  conductance term.  Lower == more '
             'preservation of image features.')]

        
        scriptedConfigModuleMixin.__init__(self, configList)


        # setup the pipeline
        if3 = itk.Image[itk.F, 3]
        d = itk.GradientAnisotropicDiffusionImageFilter[if3, if3].New()
        d.SetTimeStep(0.0625) # standard for 3D
        self._diffuse = d
        
        module_kits.itk_kit.utils.setupITKObjectProgress(
            self, self._diffuse, 'itkGradientAnisotropicDiffusionImageFilter',
            'Smoothing data')

        self._createWindow(
            {'Module (self)' : self,
             'itkGradientAnisotropicDiffusion' : self._diffuse})

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
        del self._diffuse

    def executeModule(self):
        self._diffuse.Update()

    def getInputDescriptions(self):
        return ('ITK Image (3D, float)',)

    def setInput(self, idx, inputStream):
        self._diffuse.SetInput(inputStream)

    def getOutputDescriptions(self):
        return ('ITK Image (3D, float)',)

    def getOutput(self, idx):
        return self._diffuse.GetOutput()

    def configToLogic(self):
        self._diffuse.SetNumberOfIterations(self._config.numberOfIterations)
        self._diffuse.SetConductanceParameter(
            self._config.conductanceParameter)

    def logicToConfig(self):
        self._config.numberOfIterations = self._diffuse.GetNumberOfIterations()
        self._config.conductanceParameter = self._diffuse.\
                                            GetConductanceParameter()
