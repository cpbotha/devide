# $Id: histogram2D.py,v 1.4 2004/02/19 14:36:08 cpbotha Exp $

from moduleBase import moduleBase
import moduleUtils
import vtk
import vtkdevide

class histogram2D(moduleBase):
    """This module takes two inputs and creates a 2D histogram with input 1
    vs input 2.

    The inputs have to have identical dimensions.
    """

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        self._histogram = vtkdevide.vtkImageHistogram2D()
        moduleUtils.setupVTKObjectProgress(self, self._histogram,
                                           'Calculating 2D histogram')
        

        self._input0 = None
        self._input1 = None

    def close(self):
        self.setInput(0, None)
        self.setInput(1, None)

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

    def view(self):
        pass

    # ----------------------------------------------------------------------
    # non-API methods start here -------------------------------------------
    # ----------------------------------------------------------------------
    
    def _histogramSourceExecute(self):
        """Execute callback for the vtkProgrammableSource histogram instance.
        """

        self._histogramSource 
