from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import moduleUtils
import vtk

class transformVolumeData(noConfigModuleMixin, moduleBase):
    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)
        # initialise any mixins we might have
        noConfigModuleMixin.__init__(self)


        self._imageReslice = vtk.vtkImageReslice()
        self._imageReslice.SetInterpolationModeToCubic()

        moduleUtils.setupVTKObjectProgress(self, self._imageReslice,
                                           'Resampling volume')

        self._viewFrame = self._createViewFrame(
            {'Module (self)' : self,
             'vtkImageReslice' : self._imageReslice})

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
        # don't forget to call the close() method of the vtkPipeline mixin
        noConfigModuleMixin.close(self)
        # get rid of our reference
        del self._imageReslice

    def getInputDescriptions(self):
	return ('VTK Image Data', 'VTK Transform')

    def setInput(self, idx, inputStream):
        if idx == 0:
            self._imageReslice.SetInput(inputStream)
        else:
            if inputStream == None:
                # disconnect
                self._imageReslice.SetResliceTransform(None)

            else:
                # resliceTransform transforms the resampling grid, which
                # is equivalent to transforming the volume with its inverse
                self._imageReslice.SetResliceTransform(
                    inputStream.GetInverse())

    def getOutputDescriptions(self):
        return ('Transformed VTK Image Data',)

    def getOutput(self, idx):
        return self._imageReslice.GetOutput()

    def logicToConfig(self):
        pass

    def configToLogic(self):
        pass
    

    def viewToConfig(self):
        pass

    def configToView(self):
        pass
    

    def executeModule(self):
        self._imageReslice.Update()

    
    
        
        
        
