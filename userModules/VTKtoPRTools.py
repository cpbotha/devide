from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin

class VTKtoPRTools(scriptedConfigModuleMixin, moduleBase):

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        self._config.filename = 'default.m'

        configList = [
            ('Output filename:', 'filename', 'base:str', 'filebrowser',
             'Type filename or click "browse" button to choose.')]

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

    def executeModule(self):
        pass

    def getInputDescriptions(self):
        return ('VTK Image Data (multiple components)',)

    def setInput(self, idx, inputStream):
        self._inputData = inputStream

    def getOutputDescriptions(self):
        return ()

    def getOutput(self, idx):
        raise Exception

    def configToLogic(self):
        pass

    def logicToConfig(self):
        pass

    
