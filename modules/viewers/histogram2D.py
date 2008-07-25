# $Id$

from module_base import ModuleBase
from module_mixins import ScriptedConfigModuleMixin
import module_utils
import vtk
import vtkdevide

class histogram2D(ScriptedConfigModuleMixin, ModuleBase):
    """This module takes two inputs and creates a 2D histogram with input 2
    vs input 1, i.e. input 1 on x-axis and input 2 on y-axis.

    The inputs have to have identical dimensions.
    """

    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        self._histogram = vtkdevide.vtkImageHistogram2D()
        module_utils.setupVTKObjectProgress(self, self._histogram,
                                           'Calculating 2D histogram')


        self._config.input1Bins = 256
        self._config.input2Bins = 256
        self._config.maxSamplesPerBin = 512

        configList = [
            ('Number of bins for input 1', 'input1Bins', 'base:int', 'text',
             'The full range of input 1 values will be divided into this many '
             'classes.'),
            ('Number of bins for input 2', 'input2Bins', 'base:int', 'text',
             'The full range of input 2 values will be divided into this many '
             'classes.'),
            ('Maximum samples per bin', 'maxSamplesPerBin', 'base:int', 'text',
             'The number of samples per 2D bin/class will be truncated to '
             'this value.')]

        ScriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
             'vtkImageHistogram2D' : self._histogram})

        self.sync_module_logic_with_config()

        self._input0 = None
        self._input1 = None

    def close(self):
        self.set_input(0, None)
        self.set_input(1, None)

        ScriptedConfigModuleMixin.close(self)
        ModuleBase.close(self)

        del self._histogram

    def get_input_descriptions(self):
        return ('Image Data 1', 'Imaga Data 2')

    def set_input(self, idx, inputStream):

        def checkTypeAndReturnInput(inputStream):
            """Check type of input.  None gets returned.  The input is
            returned if it has a valid type.  An exception is thrown if
            the input is invalid.
            """
            
            if inputStream == None:
                # disconnect
                return None
                
            else:
                # first check the type
                validType = False
                try:
                    if inputStream.IsA('vtkImageData'):
                        validType = True

                except AttributeError:
                    # validType is already False
                    pass

                if not validType:
                    raise TypeError, 'Input has to be of type vtkImageData.'
                else:
                    return inputStream
            
            
        if idx == 0:
            self._input0 = checkTypeAndReturnInput(inputStream)
            self._histogram.SetInput1(self._input0)

        elif idx == 1:
            self._input1 = checkTypeAndReturnInput(inputStream)
            self._histogram.SetInput2(self._input1)


    def get_output_descriptions(self):
        return (self._histogram.GetOutput().GetClassName(),)

    def get_output(self, idx):
        #raise NotImplementedError
        return self._histogram.GetOutput()

    def execute_module(self):
        self._histogram.Update()

    def logic_to_config(self):
        self._config.input1Bins = self._histogram.GetInput1Bins()
        self._config.input2Bins = self._histogram.GetInput2Bins()
        self._config.maxSamplesPerBin = self._histogram.GetMaxSamplesPerBin()
    
    def config_to_logic(self):
        self._histogram.SetInput1Bins(self._config.input1Bins)
        self._histogram.SetInput2Bins(self._config.input2Bins)
        self._histogram.SetMaxSamplesPerBin(self._config.maxSamplesPerBin)


    # ----------------------------------------------------------------------
    # non-API methods start here -------------------------------------------
    # ----------------------------------------------------------------------
    
    def _histogramSourceExecute(self):
        """Execute callback for the vtkProgrammableSource histogram instance.
        """

        self._histogramSource 
