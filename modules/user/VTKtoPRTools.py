from module_base import ModuleBase
from moduleMixins import ScriptedConfigModuleMixin
from wxPython import wx

class VTKtoPRTools(ScriptedConfigModuleMixin, ModuleBase):

    """Module to convert multi-component VTK image data to PRTools-compatible
    dataset.

    $Revision: 1.1 $
    """

    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        self._config.filename = ''

        configList = [
            ('Output filename:', 'filename', 'base:str', 'filebrowser',
             'Type filename or click "browse" button to choose.',
             {'fileMode' : wx.wxSAVE,
              'fileMask' :
              'Matlab text file (*.txt)|*.txt|All files (*.*)|*.*'})
            ]

        ScriptedConfigModuleMixin.__init__(self, configList)

        self._createViewFrame(
            {'Module (self)' : self})

        self._inputData = None

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        ScriptedConfigModuleMixin.close(self)
        # and the baseclass close
        ModuleBase.close(self)

        del self._inputData

    def execute_module(self):
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

            self._module_manager.setProgress((float(i) / (nop - 1)) * 100.0,
                                            'Exporting PRTools data.')


        self._module_manager.setProgress(100.0,
                                        'Exporting PRTools data [DONE].')
        

    def get_input_descriptions(self):
        return ('VTK Image Data (multiple components)',)

    def set_input(self, idx, inputStream):
        try:
            if inputStream == None or inputStream.IsA('vtkImageData'):
                self._inputData = inputStream
            else:
                raise AttributeError
            
        except AttributeError:
            raise TypeError, 'This module requires a vtkImageData as input.'

    def get_output_descriptions(self):
        return ()

    def get_output(self, idx):
        raise Exception

    def config_to_logic(self):
        pass

    def logic_to_config(self):
        pass

    
