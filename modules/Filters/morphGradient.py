import genUtils
from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import wx
import vtk

class morphGradient(scriptedConfigModuleMixin, moduleBase):

    """Performs a greyscale morphological gradient on the input image.

    This is done by performing an erosion and a dilation of the input image
    and then subtracting the erosion from the dilation.  The structuring
    element is ellipsoidal with user specified sizes in 3 dimensions.
    Specifying a size of 1 in any dimension will disable processing in that
    dimension.

    This module can also return both half gradients: the inner (image -
    erosion) and the outer (dilation - image).
    
    $Revision: 1.2 $
    """
    
    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)

        # main morph gradient
        self._imageDilate = vtk.vtkImageContinuousDilate3D()
        self._imageErode = vtk.vtkImageContinuousErode3D()
        self._imageMath = vtk.vtkImageMathematics()
        self._imageMath.SetOperationToSubtract()

        self._imageMath.SetInput1(self._imageDilate.GetOutput())
        self._imageMath.SetInput2(self._imageErode.GetOutput())

        # inner gradient
        self._innerImageMath = vtk.vtkImageMathematics()
        self._innerImageMath.SetOperationToSubtract()
        self._innerImageMath.SetInput1(None) # has to take image
        self._innerImageMath.SetInput2(self._imageErode.GetOutput())

        # outer gradient
        self._outerImageMath = vtk.vtkImageMathematics()
        self._outerImageMath.SetOperationToSubtract()
        self._outerImageMath.SetInput1(self._imageDilate.GetOutput()) 
        self._outerImageMath.SetInput2(None) # has to take image
        
        
        moduleUtils.setupVTKObjectProgress(self, self._imageDilate,
                                           'Performing greyscale 3D dilation')

        moduleUtils.setupVTKObjectProgress(self, self._imageErode,
                                           'Performing greyscale 3D erosion')

        moduleUtils.setupVTKObjectProgress(self, self._imageMath,
                                           'Subtracting erosion from '
                                           'dilation')

        moduleUtils.setupVTKObjectProgress(self, self._innerImageMath,
                                           'Subtracting erosion from '
                                           'image (inner)')

        moduleUtils.setupVTKObjectProgress(self, self._outerImageMath,
                                           'Subtracting image from '
                                           'dilation (outer)')
                                           
        self._config.kernelSize = (3, 3, 3)


        configList = [
            ('Kernel size:', 'kernelSize', 'tuple:int,3', 'text',
             'Size of the kernel in x,y,z dimensions.')]
        scriptedConfigModuleMixin.__init__(self, configList)        
        

        self._viewFrame = self._createWindow(
            {'Module (self)' : self,
             'vtkImageContinuousDilate3D' : self._imageDilate,
             'vtkImageContinuousErode3D' : self._imageErode,
             'vtkImageMathematics' : self._imageMath})

        # pass the data down to the underlying logic
        self.configToLogic()
        # and all the way up from logic -> config -> view to make sure
        self.syncViewWithLogic()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)

        moduleBase.close(self)
        
        # get rid of our reference
        del self._imageDilate
        del self._imageErode
        del self._imageMath

    def getInputDescriptions(self):
        return ('vtkImageData',)

    def setInput(self, idx, inputStream):
        self._imageDilate.SetInput(inputStream)
        self._imageErode.SetInput(inputStream)
        self._innerImageMath.SetInput1(inputStream)
        self._outerImageMath.SetInput2(inputStream)

    def getOutputDescriptions(self):
        return ('Morphological gradient (vtkImageData)',
                'Morphological inner gradient (vtkImageData)',
                'Morphological outer gradient (vtkImageData)')

    def getOutput(self, idx):
        if idx == 0:
            return self._imageMath.GetOutput()
        if idx == 1:
            return self._innerImageMath.GetOutput()
        else:
            return self._outerImageMath.GetOutput()

    def logicToConfig(self):
        # if the user's futzing around, she knows what she's doing...
        # (we assume that the dilate/erode pair are in sync)
        self._config.kernelSize = self._imageDilate.GetKernelSize()
    
    def configToLogic(self):
        ks = self._config.kernelSize
        self._imageDilate.SetKernelSize(ks[0], ks[1], ks[2])
        self._imageErode.SetKernelSize(ks[0], ks[1], ks[2])
    
    def executeModule(self):
        # we only execute the main gradient
        self._imageMath.Update()


