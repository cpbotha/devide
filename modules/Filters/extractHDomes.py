from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtk
import vtkdevide

class extractHDomes(scriptedConfigModuleMixin, moduleBase):
    """Extracts light structures, also known as h-domes.

    The user specifies the parameter 'h' that indicates how much brighter the
    light structures are than their surroundings.  In short, this algorithm
    performs a fast greyscale reconstruction of the input image from a marker
    that is the image - h.  The result of this reconstruction is subtracted
    from the image.

    See 'Morphological Grayscale Reconstruction in Image Analysis:
    Applications and Efficient Algorithms', Luc Vincent, IEEE Trans. on Image
    Processing, 1993.

    $Revision: 1.2 $
    """

    def __init__(self, moduleManager):
        
        moduleBase.__init__(self, moduleManager)

        self._imageMathSubtractH = vtk.vtkImageMathematics()
        self._imageMathSubtractH.SetOperationToAddConstant()
        
        self._reconstruct = vtkdevide.vtkImageGreyscaleReconstruct3D()
        # second input is marker
        self._reconstruct.SetInput(1, self._imageMathSubtractH.GetOutput())

        self._imageMathSubtractR = vtk.vtkImageMathematics()
        self._imageMathSubtractR.SetOperationToSubtract()

        self._imageMathSubtractR.SetInput(1, self._reconstruct.GetOutput())

        moduleUtils.setupVTKObjectProgress(self, self._imageMathSubtractH,
                                           'Preparing marker image.')

        moduleUtils.setupVTKObjectProgress(self, self._reconstruct,
                                           'Performing reconstruction.')

        moduleUtils.setupVTKObjectProgress(self, self._imageMathSubtractR,
                                           'Subtracting reconstruction.')

        self._config.h = 50

        configList = [
            ('H-dome height:', 'h', 'base:float', 'text',
             'The required difference in brightness between an h-dome and\n'
             'its surroundings.')]

        scriptedConfigModuleMixin.__init__(self, configList)

        self._viewFrame = self._createViewFrame(
            {'Module (self)' : self,
             'ImageMath Subtract H' : self._imageMathSubtractH,
             'ImageGreyscaleReconstruct3D' : self._reconstruct,
             'ImageMath Subtract R' : self._imageMathSubtractR})

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

        moduleBase.close(self)
        
        # get rid of our reference
        del self._imageMathSubtractH
        del self._reconstruct
        del self._imageMathSubtractR

    def getInputDescriptions(self):
        return ('Input image (VTK)',)

    def setInput(self, idx, inputStream):
        self._imageMathSubtractH.SetInput(0, inputStream)
        # first input of the reconstruction is the image
        self._reconstruct.SetInput(0, inputStream)
        self._imageMathSubtractR.SetInput(0, inputStream)

    def getOutputDescriptions(self):
        return ('h-dome extraction (VTK image)',)

    def getOutput(self, idx):
        return self._imageMathSubtractR.GetOutput()

    def logicToConfig(self):
        self._config.h = - self._imageMathSubtractH.GetConstantC()

    def configToLogic(self):
        self._imageMathSubtractH.SetConstantC( - self._config.h)

    def executeModule(self):
        self._imageMathSubtractR.Update()
        
            

        
        
        
        
    
