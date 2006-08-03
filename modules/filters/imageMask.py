from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtk


class imageMask(scriptedConfigModuleMixin, moduleBase):

    
    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)

        # setup VTK pipeline #########################################
        # 1. vtkImageMask
        self._imageMask = vtk.vtkImageMask()

        self._imageMask.GetOutput().SetUpdateExtentToWholeExtent()
        #self._imageMask.SetMaskedOutputValue(0)
        
        moduleUtils.setupVTKObjectProgress(self, self._imageMask,
                                           'Masking image')
        
        

        # 2. vtkImageCast
        self._image_cast = vtk.vtkImageCast()
        # type required by vtkImageMask
        self._image_cast.SetOutputScalarTypeToUnsignedChar()
        # connect output of cast to imagemask input
        self._imageMask.SetMaskInput(self._image_cast.GetOutput())

        moduleUtils.setupVTKObjectProgress(
            self, self._image_cast,
            'Casting mask image to unsigned char')
        
        

        ###############################################################
        

        self._config.not_mask = False
        self._config.masked_output_value = 0.0

        config_list = [
            ('Negate (NOT) mask:', 'not_mask', 'base:bool', 'checkbox',
             'Should mask be negated (NOT operator applied) before '
             'applying to input?'),
            ('Masked output value:', 'masked_output_value', 'base:float',
             'text', 'Positions outside the mask will be assigned this '
             'value.')]

        scriptedConfigModuleMixin.__init__(self, config_list)

        self._viewFrame = self._createWindow(
            {'Module (self)' :self,
             'vtkImageMask' : self._imageMask})

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
        del self._imageMask
        del self._image_cast

    def getInputDescriptions(self):
        return ('vtkImageData (data)', 'vtkImageData (mask)')

    def setInput(self, idx, inputStream):
        if idx == 0:
            self._imageMask.SetImageInput(inputStream)
        else:
            self._image_cast.SetInput(inputStream)

    def getOutputDescriptions(self):
        return (self._imageMask.GetOutput().GetClassName(), )

    def getOutput(self, idx):
        return self._imageMask.GetOutput()

    def logicToConfig(self):
        self._config.not_mask = bool(self._imageMask.GetNotMask())

        # GetMaskedOutputValue() is not wrapped.  *SIGH*
        #self._config.masked_output_value = \
        #                     self._imageMask.GetMaskedOutputValue()
        
    
    def configToLogic(self):
        self._imageMask.SetNotMask(self._config.not_mask)
        self._imageMask.SetMaskedOutputValue(self._config.masked_output_value)
    
    def executeModule(self):
        self._imageMask.Update()
        


