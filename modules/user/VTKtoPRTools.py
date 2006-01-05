from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
from wxPython import wx

class VTKtoPRTools(scriptedConfigModuleMixin, moduleBase):

    """Module to convert multi-component VTK image data to PRTools-compatible
    dataset.

    $Revision: 1.1 $
    """

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        self._config.filename = ''

        configList = [
            ('Output filename:', 'filename', 'base:str', 'filebrowser',
             'Type filename or click "browse" button to choose.',
             {'fileMode' : wx.wxSAVE,
              'fileMask' :
              'Matlab text file (*.txt)|*.txt|All files (*.*)|*.*'})
            ]

        scriptedConfigModuleMixin.__init__(self, configList)

        self._createViewFrame(
            {'Module (self)' : self})

        self._inputData = None

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)
        # and the baseclass close
        moduleBase.close(self)

        del self._inputData

    def executeModule(self):
        # this is where the good stuff happens...

        if len(self._config.filename) == 0:
            raise RuntimeError, 'No filename has been set.'

        if self._inputData == None:
            raise RuntimeError, 'No input data to convert.'

        # now let's start going through the data
        outfile = file(self._config.filename, 'w')
        self._inputData.Update()

        nop = self._inputData.GetNumberOfPoints()
        noc = self._inputData.GetNumberOfScalarComponents()
        pd = self._inputData.GetPointData()
        curList = [''] * noc

        for i in xrange(nop):
            for j in range(noc):
                curList[j] = str(pd.GetComponent(i, j))

            outfile.write('%s\n' % (' '.join(curList),))

            self._moduleManager.setProgress((float(i) / (nop - 1)) * 100.0,
                                            'Exporting PRTools data.')


        self._moduleManager.setProgress(100.0,
                                        'Exporting PRTools data [DONE].')
        

    def getInputDescriptions(self):
        return ('VTK Image Data (multiple components)',)

    def setInput(self, idx, inputStream):
        try:
            if inputStream == None or inputStream.IsA('vtkImageData'):
                self._inputData = inputStream
            else:
                raise AttributeError
            
        except AttributeError:
            raise TypeError, 'This module requires a vtkImageData as input.'

    def getOutputDescriptions(self):
        return ()

    def getOutput(self, idx):
        raise Exception

    def configToLogic(self):
        pass

    def logicToConfig(self):
        pass

    
