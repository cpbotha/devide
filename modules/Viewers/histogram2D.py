# $Id: histogram2D.py,v 1.3 2004/02/18 17:29:49 cpbotha Exp $

from moduleBase import moduleBase
import vtk
import vtkdevide

class histogram2D(moduleBase):
    """This module takes two inputs and creates a 2D histogram with input 1
    vs input 2.

    The inputs have to have identical dimensions.
    """

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        self._histogramSource = vtk.vtkProgrammableSource()

        self.setInput(0, None)
        self.setInput(1, None)
        
        pass

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
            
            
        if idx == 0:
            self._input0 = checkTypeAndReturnInput(inputStream)

        elif idx == 1:
            self._input1 = checkTypeAndReturnInput(inputStream)


    def getOutputDescriptions(self):
        return ()

    def getOutput(self, idx):
        raise NotImplementedError

    def executeModule(self):
        pass

    def view(self):
        pass

    # ----------------------------------------------------------------------
    # non-API methods start here -------------------------------------------
    # ----------------------------------------------------------------------
    
    def _histogramSourceExecute(self):
        """Execute callback for the vtkProgrammableSource histogram instance.
        """

        self._histogramSource 
