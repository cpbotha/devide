# $Id: histogram2D.py,v 1.1 2004/02/18 15:38:41 cpbotha Exp $

from moduleBase import moduleBase

class histogram2D(moduleBase):
    """This module takes two inputs and creates a 2D histogram with input 1
    vs input 2.

    The inputs have to have identical dimensions.
    """

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)
        pass

    def close(self):
        self.setInput(0, None)
        self.setInput(1, None)

        moduleBase.close(self)

    def getInputDescriptions(self):
        return ('Image Data 1', 'Imaga Data 2')

    def setInput(self, idx, inputStream):
        pass

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
    
