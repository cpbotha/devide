# $Id$

import itk
import module_kits.itk_kit as itk_kit
from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin

class curvatureFlowDenoising(scriptedConfigModuleMixin, moduleBase):
    
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
        if3 = itk.Image[itk.F, 3]
        self._cfif = itk.CurvatureFlowImageFilter[if3, if3].New()
        
        itk_kit.utils.setupITKObjectProgress(
            self, self._cfif, 'itkCurvatureFlowImageFilter',
            'Denoising data')

        self._createWindow(
            {'Module (self)' : self,
             'itkCurvatureFlowImageFilter' : self._cfif})

        self.config_to_logic()
        self.logic_to_config()
        self.config_to_view()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)
        # and the baseclass close
        moduleBase.close(self)
            
        # remove all bindings
        del self._cfif

    def execute_module(self):
        self._cfif.Update()
        self._moduleManager.setProgress(100, "Denoising data [DONE]")

    def get_input_descriptions(self):
        return ('ITK Image (3D, float)',)

    def set_input(self, idx, inputStream):
        self._cfif.SetInput(inputStream)

    def get_output_descriptions(self):
        return ('Denoised ITK Image (3D, float)',)

    def get_output(self, idx):
        return self._cfif.GetOutput()

    def config_to_logic(self):
        self._cfif.SetNumberOfIterations(self._config.numberOfIterations)
        self._cfif.SetTimeStep(self._config.timeStep)

    def logic_to_config(self):
        self._config.numberOfIterations = self._cfif.GetNumberOfIterations()
        self._config.timeStep = self._cfif.GetTimeStep()
        
                                          
