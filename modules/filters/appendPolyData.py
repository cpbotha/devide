import genUtils
from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import moduleUtils
import vtk


class appendPolyData(moduleBase, noConfigModuleMixin):
    """DeVIDE encapsulation of the vtkAppendPolyDataFilter that enables us
    to combine multiple PolyData structures into one.

    DANGER WILL ROBINSON: contact the author, this module is BROKEN.

    $Revision: 1.6 $
    """

    _numInputs = 5
    
    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)
        noConfigModuleMixin.__init__(self)

        # underlying VTK thingy
        self._appendPolyData = vtk.vtkAppendPolyData()
        # our own list of inputs
        self._inputStreams = self._numInputs * [None]

        moduleUtils.setupVTKObjectProgress(self, self._appendPolyData,
                                           'Appending PolyData')
        

        self._viewFrame = self._createViewFrame(
            {'vtkAppendPolyData' : self._appendPolyData})

        # pass the data down to the underlying logic
        self.configToLogic()
        # and all the way up from logic -> config -> view to make sure
        self.logicToConfig()
        self.configToView()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)

        # this will take care of all display thingies
        noConfigModuleMixin.close(self)
        
        # get rid of our reference
        del self._appendPolyData

    def getInputDescriptions(self):
        return self._numInputs * ('vtkPolyData',)

    def setInput(self, idx, inputStream):
        # only do something if we don't have this already
        if self._inputStreams[idx] != inputStream:

            if inputStream:
                # add it                
                self._appendPolyData.AddInput(inputStream)
            else:
                # or remove it
                self._appendPolyData.RemoveInput(inputStream)

            # whatever the case, record it
            self._inputStreams[idx] = inputStream
        
    def getOutputDescriptions(self):
        return (self._appendPolyData.GetOutput().GetClassName(), )

    def getOutput(self, idx):
        return self._appendPolyData.GetOutput()

    def logicToConfig(self):
        pass
    
    def configToLogic(self):
        pass
    
    def viewToConfig(self):
        pass

    def configToView(self):
        pass
    
    def executeModule(self):
        self._appendPolyData.Update()
        

    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()

