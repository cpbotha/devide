# $Id: histogram2D.py,v 1.6 2004/03/19 14:25:43 cpbotha Exp $

from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtk
import vtkdevide

class histogram2D(scriptedConfigModuleMixin, moduleBase):
    """This module takes two inputs and creates a 2D histogram with input 1
    vs input 2.

    The inputs have to have identical dimensions.
    """

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        self._histogram = vtkdevide.vtkImageHistogram2D()
        moduleUtils.setupVTKObjectProgress(self, self._histogram,
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

        scriptedConfigModuleMixin.__init__(self, configList)

        self._viewFrame = self._createWindow(
            {'Module (self)' : self,
             'vtkImageHistogram2D' : self._histogram})

        # pass the data down to the underlying logic
        self.configToLogic()
        # and all the way up from logic -> config -> view to make sure
        self.syncViewWithLogic()

        self._input0 = None
        self._input1 = None

    def close(self):
        self.setInput(0, None)
        self.setInput(1, None)

        scriptedConfigModuleMixin.close(self)
        moduleBase.close(self)

    def getInputDescriptions(self):
        return ('Image Data 1', 'Imaga Data 2')

    def setInput(self, idx, inputStream):

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


    def getOutputDescriptions(self):
        return (self._histogram.GetOutput().GetClassName(),)

    def getOutput(self, idx):
        #raise NotImplementedError
        return self._histogram.GetOutput()

    def executeModule(self):
        self._histogram.Update()

    def logicToConfig(self):
        self._config.input1Bins = self._histogram.GetInput1Bins()
        self._config.input2Bins = self._histogram.GetInput2Bins()
        self._config.maxSamplesPerBin = self._histogram.GetMaxSamplesPerBin()
    
    def configToLogic(self):
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
