import genUtils
from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtk


class imageGreyErode(scriptedConfigModuleMixin, moduleBase):

    """Performs a greyscale 3D erosion on the input.
    
    $Revision: 1.2 $
    """
    
    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)


        self._imageErode = vtk.vtkImageContinuousErode3D()
        
        moduleUtils.setupVTKObjectProgress(self, self._imageErode,
                                           'Performing greyscale 3D erosion')
        
                                           
        self._config.kernelSize = (3, 3, 3)


        configList = [
            ('Kernel size:', 'kernelSize', 'tuple:int,3', 'text',
             'Size of the kernel in x,y,z dimensions.')]
        scriptedConfigModuleMixin.__init__(self, configList)        
        

        self._viewFrame = self._createWindow(
            {'Module (self)' : self,
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
        del self._imageErode

    def getInputDescriptions(self):
        return ('vtkImageData',)

    def setInput(self, idx, inputStream):
        self._imageErode.SetInput(inputStream)

    def getOutputDescriptions(self):
        return (self._imageErode.GetOutput().GetClassName(), )

    def getOutput(self, idx):
        return self._imageErode.GetOutput()

    def logicToConfig(self):
        self._config.kernelSize = self._imageErode.GetKernelSize()
    
    def configToLogic(self):
        ks = self._config.kernelSize
        self._imageErode.SetKernelSize(ks[0], ks[1], ks[2])
    
    def executeModule(self):
        self._imageErode.Update()
        

    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        self._viewFrame.Show(True)
        self._viewFrame.Raise()


