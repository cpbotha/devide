import genUtils
from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtk
from module_kits.vtk_kit.mixins import VTKErrorFuncMixin

class opening(scriptedConfigModuleMixin, moduleBase, VTKErrorFuncMixin):

    """Performs a greyscale morphological opening on the input image.

    Erosion is followed by dilation.  The structuring element is ellipsoidal
    with user specified sizes in 3 dimensions.  Specifying a size of 1 in any
    dimension will disable processing in that dimension.

    $Revision: 1.2 $
    """
    
    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)

        self._imageDilate = vtk.vtkImageContinuousDilate3D()
        self._imageErode = vtk.vtkImageContinuousErode3D()
        self._imageDilate.SetInput(self._imageErode.GetOutput())
        
        moduleUtils.setupVTKObjectProgress(self, self._imageDilate,
                                           'Performing greyscale 3D dilation')
        self.add_vtk_error_handler(self._imageDilate)

        moduleUtils.setupVTKObjectProgress(self, self._imageErode,
                                           'Performing greyscale 3D erosion')
        self.add_vtk_error_handler(self._imageErode)

        self._config.kernelSize = (3, 3, 3)


        configList = [
            ('Kernel size:', 'kernelSize', 'tuple:int,3', 'text',
             'Size of the kernel in x,y,z dimensions.')]
        scriptedConfigModuleMixin.__init__(self, configList)        
        

        self._viewFrame = self._createWindow(
            {'Module (self)' : self,
             'vtkImageContinuousDilate3D' : self._imageDilate,
             'vtkImageContinuousErode3D' : self._imageErode})
   
        # pass the data down to the underlying logic
        self.configToLogic()
        # and all the way up from logic -> config -> view to make sure
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
        del self._imageDilate
        del self._imageErode

    def getInputDescriptions(self):
        return ('vtkImageData',)

    def setInput(self, idx, inputStream):
        self._imageErode.SetInput(inputStream)

    def getOutputDescriptions(self):
        return ('Opened image (vtkImageData)',)

    def getOutput(self, idx):
        return self._imageDilate.GetOutput()

    def logicToConfig(self):
        # if the user's futzing around, she knows what she's doing...
        # (we assume that the dilate/erode pair are in sync)
        self._config.kernelSize = self._imageErode.GetKernelSize()
    
    def configToLogic(self):
        ks = self._config.kernelSize
        self._imageDilate.SetKernelSize(ks[0], ks[1], ks[2])
        self._imageErode.SetKernelSize(ks[0], ks[1], ks[2])
    
    def executeModule(self):
        self._imageErode.Update()
        self.check_vtk_error()
        self._imageDilate.Update()
        self.check_vtk_error()


