import genUtils
from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtk
from module_kits.vtk_kit.mixins import VTKErrorFuncMixin

class DilateExample(scriptedConfigModuleMixin, moduleBase,
                    VTKErrorFuncMixin):

    """Performs a greyscale 3D dilation on the input.
    
    $Revision: 1.2 $
    """
    
    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)


        self._imageDilate = vtk.vtkImageContinuousDilate3D()
        
        moduleUtils.setupVTKObjectProgress(self, self._imageDilate,
                                           'Performing greyscale 3D dilation')
        self.add_vtk_error_handler(self._imageDilate)
                                           
        self._config.kernelSize = (3, 3, 3)


        configList = [
            ('Kernel size:', 'kernelSize', 'tuple:int,3', 'text',
             'Size of the kernel in x,y,z dimensions.')]
        scriptedConfigModuleMixin.__init__(self, configList)        
        

        self._viewFrame = self._createWindow(
            {'Module (self)' : self,
             'vtkImageContinuousDilate3D' : self._imageDilate})

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

    def getInputDescriptions(self):
        return ('vtkImageData',)

    def setInput(self, idx, inputStream):
        self._imageDilate.SetInput(inputStream)

    def getOutputDescriptions(self):
        return (self._imageDilate.GetOutput().GetClassName(), )

    def getOutput(self, idx):
        return self._imageDilate.GetOutput()

    def logicToConfig(self):
        self._config.kernelSize = self._imageDilate.GetKernelSize()
    
    def configToLogic(self):
        ks = self._config.kernelSize
        self._imageDilate.SetKernelSize(ks[0], ks[1], ks[2])
    
    def executeModule(self):
        self._imageDilate.Update()
        self.check_vtk_error()

    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        self._viewFrame.Show(True)
        self._viewFrame.Raise()


