import genUtils
from module_base import ModuleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtk


class seedConnect(scriptedConfigModuleMixin, ModuleBase):

    def __init__(self, moduleManager):

        # call parent constructor
        ModuleBase.__init__(self, moduleManager)

        self._imageCast = vtk.vtkImageCast()
        self._imageCast.SetOutputScalarTypeToUnsignedChar()
        self._seedConnect = vtk.vtkImageSeedConnectivity()
        self._seedConnect.SetInput(self._imageCast.GetOutput())

        moduleUtils.setupVTKObjectProgress(self, self._seedConnect,
                                           'Performing region growing')
        
        
        moduleUtils.setupVTKObjectProgress(self, self._imageCast,
                                           'Casting data to unsigned char')
        
        
        # we'll use this to keep a binding (reference) to the passed object
        self._inputPoints = None
        # this will be our internal list of points
        self._seedPoints = []

        # now setup some defaults before our sync
        self._config.inputConnectValue = 1
        self._config.outputConnectedValue = 1
        self._config.outputUnconnectedValue = 0


        config_list = [
            ('Input connect value:', 'inputConnectValue', 'base:int', 'text',
             'Points connected to seed points with this value will be '
             'included.'),
            ('Output connected value:', 'outputConnectedValue', 'base:int',
             'text', 'Included points will get this value.'),
            ('Output unconnected value:', 'outputUnconnectedValue',
             'base:int', 'text', 'Non-included points will get this value.')]
             
        scriptedConfigModuleMixin.__init__(
            self, config_list,
            {'Module (self)' : self,
             'vtkImageSeedConnectivity' : self._seedConnect,
             'vtkImageCast' : self._imageCast})

        self.sync_module_logic_with_config()
        
    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        self.set_input(0, None)
        self.set_input(1, None)
        # don't forget to call the close() method of the vtkPipeline mixin
        scriptedConfigModuleMixin.close(self)

        # get rid of our reference
        del self._imageCast
        self._seedConnect.SetInput(None)
        del self._seedConnect

    def get_input_descriptions(self):
        return ('vtkImageData', 'Seed points')
    
    def set_input(self, idx, inputStream):
        if idx == 0:
            # will work for None and not-None
            self._imageCast.SetInput(inputStream)
        else:
            if inputStream != self._inputPoints:
                self._inputPoints = inputStream
    
    def get_output_descriptions(self):
        return ('Region growing result (vtkImageData)',)
    
    def get_output(self, idx):
        return self._seedConnect.GetOutput()

    def logic_to_config(self):
        self._config.inputConnectValue = self._seedConnect.\
                                         GetInputConnectValue()
        self._config.outputConnectedValue = self._seedConnect.\
                                            GetOutputConnectedValue()
        self._config.outputUnconnectedValue = self._seedConnect.\
                                              GetOutputUnconnectedValue()

    def config_to_logic(self):
        self._seedConnect.SetInputConnectValue(self._config.inputConnectValue)
        self._seedConnect.SetOutputConnectedValue(self._config.\
                                                  outputConnectedValue)
        self._seedConnect.SetOutputUnconnectedValue(self._config.\
                                                    outputUnconnectedValue)

    def execute_module(self):
        self._sync_to_input_points()
        self._seedConnect.Update()
        
    # we can't stream this module, as it needs up to date seed points
    # before it begins.

    def _sync_to_input_points(self):
        # extract a list from the input points
        tempList = []
        if self._inputPoints:
            for i in self._inputPoints:
                tempList.append(i['discrete'])

        if tempList != self._seedPoints:
            self._seedPoints = tempList
            self._seedConnect.RemoveAllSeeds()
            # we need to call Modified() explicitly as RemoveAllSeeds()
            # doesn't.  AddSeed() does, but sometimes the list is empty at
            # this stage and AddSeed() isn't called.
            self._seedConnect.Modified()
            
            for seedPoint in self._seedPoints:
                self._seedConnect.AddSeed(seedPoint[0], seedPoint[1],
                                          seedPoint[2])




