from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtkLocalPython
import wx

class imageSepConvolution(scriptedConfigModuleMixin, moduleBase):
    """
            lksajflksjdf
    """
    
    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)

        self._imageSepConvolution = vtkLocalPython.vtkImageSepConvolution()

#        moduleUtils.setupVTKObjectProgress(self, self._clipper,
#                                           'Reading PNG images.')

        # set information for scriptedConfigModuleMixin
        self._config.axis = 0

        # FIXME: include options for kernel normalisation?
        configList = [
            ('Axis:', 'axis', 'base:int', 'choice',
             'Axis over which convolution is to be performed.', ("X", "Y", "Z") ) ] 

        scriptedConfigModuleMixin.__init__(self, configList)

        self._viewFrame = self._createViewFrame(
            {'Module (self)' : self,
             'vtkImageSepConvolution' : self._imageSepConvolution})

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
        del self._imageSepConvolution

    def getInputDescriptions(self):
        return ('vtkImageData', 'vtkSeparableKernel')

    def setInput(self, idx, inputStream):
        if idx == 0:
            self._imageSepConvolution.SetInput(inputStream)
        else:
            self._imageSepConvolution.SetKernel(inputStream)
            

    def getOutputDescriptions(self):
        return (self._imageSepConvolution.GetOutput().GetClassName(), )

    def getOutput(self, idx):
        return self._imageSepConvolution.GetOutput()

    def logicToConfig(self):
        self._config.axis = self._imageSepConvolution.GetAxis()
    
    def configToLogic(self):
        self._imageSepConvolution.SetAxis( self._config.axis )
    
    def executeModule(self):
        self._imageSepConvolution.Update()
