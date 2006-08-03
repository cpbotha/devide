# $Id$

import itk
import module_kits.itk_kit as itk_kit
from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin

class discreteLaplacian(noConfigModuleMixin, moduleBase):
    
    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)
        noConfigModuleMixin.__init__(self)

        # setup the pipeline
        if3 = itk.Image[itk.F, 3]
        self._laplacian = itk.LaplacianImageFilter[if3,if3].New()
        
        itk_kit.utils.setupITKObjectProgress(
            self, self._laplacian,
            'itkLaplacianImageFilter',
            'Calculating Laplacian')

        self._createViewFrame(
            {'Module (self)' : self,
             'itkLaplacianImageFilter' :
             self._laplacian})

        self.configToLogic()
        self.logicToConfig()
        self.configToView()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)

        # this will take care of all display thingies
        noConfigModuleMixin.close(self)
        # and the baseclass close
        moduleBase.close(self)
            
        # remove all bindings
        del self._laplacian

    def executeModule(self):
        self._laplacian.Update()

    def getInputDescriptions(self):
        return ('Image (ITK, 3D, float)',)

    def setInput(self, idx, inputStream):
        self._laplacian.SetInput(inputStream)

    def getOutputDescriptions(self):
        return ('Laplacian image (ITK, 3D, float)',)    

    def getOutput(self, idx):
        return self._laplacian.GetOutput()

