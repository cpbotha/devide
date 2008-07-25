from module_base import ModuleBase
from moduleMixins import ScriptedConfigModuleMixin
import module_utils
import vtk

class imageMask(ScriptedConfigModuleMixin, ModuleBase):

    
    def __init__(self, module_manager):
        # initialise our base class
        ModuleBase.__init__(self, module_manager)

        # setup VTK pipeline #########################################
        # 1. vtkImageMask
        self._imageMask = vtk.vtkImageMask()

        self._imageMask.GetOutput().SetUpdateExtentToWholeExtent()
        #self._imageMask.SetMaskedOutputValue(0)
        
        module_utils.setupVTKObjectProgress(self, self._imageMask,
                                           'Masking image')
        
        

        # 2. vtkImageCast
        self._image_cast = vtk.vtkImageCast()
        # type required by vtkImageMask
        self._image_cast.SetOutputScalarTypeToUnsignedChar()
        # connect output of cast to imagemask input
        self._imageMask.SetMaskInput(self._image_cast.GetOutput())

        module_utils.setupVTKObjectProgress(
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

        ScriptedConfigModuleMixin.__init__(
            self, config_list,
            {'Module (self)' :self,
             'vtkImageMask' : self._imageMask})
        
        self.sync_module_logic_with_config()
        
    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        ScriptedConfigModuleMixin.close(self)

        ModuleBase.close(self)
        
        # get rid of our reference
        del self._imageMask
        del self._image_cast

    def get_input_descriptions(self):
        return ('vtkImageData (data)', 'vtkImageData (mask)')

    def set_input(self, idx, inputStream):
        if idx == 0:
            self._imageMask.SetImageInput(inputStream)
        else:
            self._image_cast.SetInput(inputStream)

    def get_output_descriptions(self):
        return (self._imageMask.GetOutput().GetClassName(), )

    def get_output(self, idx):
        return self._imageMask.GetOutput()

    def logic_to_config(self):
        self._config.not_mask = bool(self._imageMask.GetNotMask())

        # GetMaskedOutputValue() is not wrapped.  *SIGH*
        #self._config.masked_output_value = \
        #                     self._imageMask.GetMaskedOutputValue()
        
    
    def config_to_logic(self):
        self._imageMask.SetNotMask(self._config.not_mask)
        self._imageMask.SetMaskedOutputValue(self._config.masked_output_value)
    
    def execute_module(self):
        self._imageMask.Update()
        


