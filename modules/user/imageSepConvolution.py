from module_base import ModuleBase
from moduleMixins import ScriptedConfigModuleMixin
import module_utils
import vtktud
import wx

class imageSepConvolution(ScriptedConfigModuleMixin, ModuleBase):
    """
            lksajflksjdf
    """
    
    def __init__(self, module_manager):
        # initialise our base class
        ModuleBase.__init__(self, module_manager)

        self._imageSepConvolution = vtktud.vtkImageSepConvolution()

#        module_utils.setupVTKObjectProgress(self, self._clipper,
#                                           'Reading PNG images.')

        # set information for ScriptedConfigModuleMixin
        self._config.axis = 0

        # FIXME: include options for kernel normalisation?
        configList = [
            ('Axis:', 'axis', 'base:int', 'choice',
             'Axis over which convolution is to be performed.', ("X", "Y", "Z") ) ] 

        ScriptedConfigModuleMixin.__init__(self, configList)

        self._viewFrame = self._createViewFrame(
            {'Module (self)' : self,
             'vtkImageSepConvolution' : self._imageSepConvolution})

        # pass the data down to the underlying logic
        self.config_to_logic()
        # and all the way up from logic -> config -> view to make sure
        self.syncViewWithLogic()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        ScriptedConfigModuleMixin.close(self)
        ModuleBase.close(self)

        # get rid of our reference
        del self._imageSepConvolution

    def get_input_descriptions(self):
        return ('vtkImageData', 'vtkSeparableKernel')

    def set_input(self, idx, inputStream):
        if idx == 0:
            self._imageSepConvolution.SetInput(inputStream)
        else:
            self._imageSepConvolution.SetKernel(inputStream)
            

    def get_output_descriptions(self):
        return (self._imageSepConvolution.GetOutput().GetClassName(), )

    def get_output(self, idx):
        return self._imageSepConvolution.GetOutput()

    def logic_to_config(self):
        self._config.axis = self._imageSepConvolution.GetAxis()
    
    def config_to_logic(self):
        self._imageSepConvolution.SetAxis( self._config.axis )
    
    def execute_module(self):
        self._imageSepConvolution.Update()
