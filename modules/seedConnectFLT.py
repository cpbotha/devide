# TODO: vtkImageCast - cast whatever to unsigned char output


import genUtils
from moduleBase import moduleBase
from moduleMixins import vtkPipelineConfigModuleMixin
import moduleUtils
from wxPython.wx import *
import vtk

class seedConnectFLT(moduleBase, vtkPipelineConfigModuleMixin):

    def __init__(self, moduleManager):

        # call parent constructor
        moduleBase.__init__(self, moduleManager)

        self._imageCast = vtk.vtkImageCast()
        self._imageCast.SetOutputScalarTypeToUnsignedChar()
        self._seedConnect = vtk.vtkImageSeedConnectivity()
        self._seedConnect.SetInput(self._imageCast.GetOutput())

        # following is the standard way of connecting up the dscas3 progress
        # callback to a VTK object; you should do this for all objects in
        # your module
        self._seedConnect.SetProgressText('performing region growing')
        mm = self._moduleManager
        self._seedConnect.SetProgressMethod(lambda s=self, mm=mm:
                                               mm.vtk_progress_cb(
            s._seedConnect))

        self._imageCast.SetProgressText('casting data to unsigned char')
        mm = self._moduleManager
        self._imageCast.SetProgressMethod(lambda s=self, mm=mm:
                                               mm.vtk_progress_cb(
            s._imageCast))
        
        
        # we'll use this to keep a binding (reference) to the passed object
        self._vtkPoints = None
        self._vtkPointsOID = -1
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

        # off we go!
        self.view()
        
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
	return ('vtkImageData', 'Seed points (vtkPoints)')
    
    def setInput(self, idx, inputStream):
        if idx == 0:
            # will work for None and not-None
            self._imageCast.SetInput(inputStream)
        else:
            if inputStream is None:
                if self._vtkPointsOID >= 0:
                    self._vtkPoints.RemoveObserver(self._vtkPointsOID)
                    self._vtkPointsOID = -1
                
            else:
                oid = inputStream.AddObserver('ModifiedEvent',
                                              self.\
                                              _vtkPointsModifiedCallback)
                self._vtkPointsOID = oid

            self._vtkPoints = inputStream

            self._vtkPointsModifiedCallback(None, None)
    
    def getOutputDescriptions(self):
	return (self._seedConnect.GetOutput().GetClassName(),)
    
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

        # tell the vtk log file window to poll the file; if the file has
        # changed, i.e. vtk has written some errors, the log window will
        # pop up.  you should do this in all your modules right after you
        # caused some VTK processing which might have resulted in VTK
        # outputting to the error log
        self._moduleManager.vtk_poll_error()

    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        if not self._viewFrame.Show(true):
            self._viewFrame.Raise()

    def _createViewFrame(self):

        # import the viewFrame (created with wxGlade)
        import modules.resources.python.seedConnectFLTViewFrame
        reload(modules.resources.python.seedConnectFLTViewFrame)

        # find our parent window and instantiate the frame
        pw = self._moduleManager.get_module_view_parent_window()
        self._viewFrame = modules.resources.python.seedConnectFLTViewFrame.\
                          seedConnectFLTViewFrame(pw, -1, 'dummy')

        # make sure that a close of that window does the right thing
        EVT_CLOSE(self._viewFrame,
                  lambda e, s=self: s._viewFrame.Show(false))

        # default binding for the buttons at the bottom
        moduleUtils.bindCSAEO(self, self._viewFrame)        

    def vtkObjectChoiceCallback(self, event):
        self.vtkObjectConfigure(self._viewFrame, None,
                                self._seedConnect)

    def vtkPipelineCallback(self, event):
        # move this to module utils too, or to base...
        self.vtkPipelineConfigure(self._viewFrame, None,
                                  (self._seedConnect,))

    def _vtkPointsModifiedCallback(self, event, obj):
        # extract a list from the input vtkPoints
        tempList = []
        if self._vtkPoints:
            for i in range(self._vtkPoints.GetNumberOfPoints() / 2):
                tempList.append(self._vtkPoints.GetPoint(i*2))

        if tempList != self._seedPoints:
            self._seedPoints = tempList
            self._seedConnect.RemoveAllSeeds()
            for seedPoint in self._seedPoints:
                self._seedConnect.AddSeed(seedPoint[0], seedPoint[1],
                                          seedPoint[2])
                print "adding %s" % (str(seedPoint))



