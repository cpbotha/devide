import genUtils
from moduleBase import moduleBase
from moduleMixins import vtkPipelineConfigModuleMixin
import moduleUtils
from wxPython.wx import *
import vtk

class seedConnect(moduleBase, vtkPipelineConfigModuleMixin):
    """3D region growing.

    Finds all points connected to the seed points that also have values
    equal to the 'Input Connected Value'.  This module casts all input to
    unsigned char.  The output is also unsigned char.

    $Revision: 1.8 $
    """

    def __init__(self, moduleManager):

        # call parent constructor
        moduleBase.__init__(self, moduleManager)

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

        self._viewFrame = None
        self._createViewFrame()

        # transfer these defaults to the logic
        self.configToLogic()

        # then make sure they come all the way back up via self._config
        self.syncViewWithLogic()
        
    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        self.setInput(0, None)
        self.setInput(1, None)
        # don't forget to call the close() method of the vtkPipeline mixin
        vtkPipelineConfigModuleMixin.close(self)
        # take out our view interface
        self._viewFrame.Destroy()
        # get rid of our reference
        del self._imageCast
        self._seedConnect.SetInput(None)
        del self._seedConnect

    def getInputDescriptions(self):
        return ('vtkImageData', 'Seed points')
    
    def setInput(self, idx, inputStream):
        if idx == 0:
            # will work for None and not-None
            self._imageCast.SetInput(inputStream)
        else:
            if inputStream != self._inputPoints:
                if self._inputPoints != None:
                    self._inputPoints.removeObserver(self._inputPointsObserver)

                if inputStream != None:
                    inputStream.addObserver(
                        self._inputPointsObserver)

                self._inputPoints = inputStream

                # initial update
                self._inputPointsObserver(None)
            
    
    def getOutputDescriptions(self):
        return ('Region growing result (vtkImageData)',)
    
    def getOutput(self, idx):
        return self._seedConnect.GetOutput()

    def logicToConfig(self):
        self._config.inputConnectValue = self._seedConnect.\
                                         GetInputConnectValue()
        self._config.outputConnectedValue = self._seedConnect.\
                                            GetOutputConnectedValue()
        self._config.outputUnconnectedValue = self._seedConnect.\
                                              GetOutputUnconnectedValue()

    def configToLogic(self):
        self._seedConnect.SetInputConnectValue(self._config.inputConnectValue)
        self._seedConnect.SetOutputConnectedValue(self._config.\
                                                  outputConnectedValue)
        self._seedConnect.SetOutputUnconnectedValue(self._config.\
                                                    outputUnconnectedValue)

    def viewToConfig(self):
        try:
            icv = int(self._viewFrame.inputConnectValueText.GetValue())
        except ValueError:
            icv = self._config.inputConnectValue

        try:
            ocv = int(self._viewFrame.outputConnectedValueText.GetValue())
        except ValueError:
            ocv = self._config.outputConnectedValue

        try:
            ouv = int(self._viewFrame.outputUnconnectedValueText.GetValue())
        except ValueError:
            ouv = self._config.outputUnconnectedValue
            
        self._config.inputConnectValue = icv
        self._config.outputConnectedValue = ocv
        self._config.outputUnconnectedValue = ouv

    def configToView(self):
        icv = str(self._config.inputConnectValue)
        self._viewFrame.inputConnectValueText.SetValue(icv)
        ocv = str(self._config.outputConnectedValue)        
        self._viewFrame.outputConnectedValueText.SetValue(ocv)
        ouv = str(self._config.outputUnconnectedValue)
        self._viewFrame.outputUnconnectedValueText.SetValue(ouv)

    def executeModule(self):
        self._seedConnect.Update()

    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()

    def _createViewFrame(self):

        # import the viewFrame (created with wxGlade)
        import modules.Filters.resources.python.seedConnectFLTViewFrame
        reload(modules.Filters.resources.python.seedConnectFLTViewFrame)

        self._viewFrame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager,
            modules.Filters.resources.python.seedConnectFLTViewFrame.\
            seedConnectFLTViewFrame)

        objectDict = {'imageCast' : self._imageCast,
                      'seedConnect' : self._seedConnect}
        moduleUtils.createStandardObjectAndPipelineIntrospection(
            self, self._viewFrame, self._viewFrame.viewFramePanel,
            objectDict, None)

        moduleUtils.createECASButtons(self, self._viewFrame,
                                      self._viewFrame.viewFramePanel)

    def _inputPointsObserver(self, obj):
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




