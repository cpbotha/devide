# $Id$

import fixitk as itk
import genUtils
from moduleBase import moduleBase
import moduleUtils
import moduleUtilsITK
from moduleMixins import noConfigModuleMixin

class discreteLaplacian(noConfigModuleMixin, moduleBase):
    """Calculates Laplacian of input image.

    This makes use of a discrete implementation.  Due to this, the input
    image should probably be pre-smoothed with e.g. a Gaussian as the
    Laplacian is very sensitive to noise.

    Note: One could also calculate the Laplacian by convolving with the
    second derivative of a Gaussian.

    Laplacian == secondPartialDerivative(f,x0) + ... +
    secondPartialDerivative(f,xn)

    $Revision: 1.2 $
    """
    
    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)
        noConfigModuleMixin.__init__(self)

        # setup the pipeline
        self._laplacian = itk.itkLaplacianImageFilterF3F3_New()
        
        moduleUtilsITK.setupITKObjectProgress(
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

