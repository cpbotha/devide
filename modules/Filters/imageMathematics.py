import genUtils
from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtk

class imageMathematics(scriptedConfigModuleMixin, moduleBase):

    """Performs point-wise mathematical operations on one or two images.

    The underlying logic can do far more than the UI shows at this moment.
    Please let me know if you require more options.
    
    $Revision: 1.2 $
    """

    _operations = {'Add' : 0,
                   'Subtract' : 1}
    
    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)


        self._imageMath = vtk.vtkImageMathematics()
        self._imageMath.SetInput1(None)
        self._imageMath.SetInput2(None)
        
        moduleUtils.setupVTKObjectProgress(self, self._imageMath,
                                           'Performing image math')
                                           
        self._config.operation = 'Subtract'


        configList = [
            ('Operation:', 'operation', 'base:str', 'choice',
             'The operation that should be performed.',
             ('Add', 'Subtract'))]

        scriptedConfigModuleMixin.__init__(self, configList)        
        

        self._viewFrame = self._createWindow(
            {'Module (self)' : self,
             'vtkImageMathematics' : self._imageMath})

        # pass the data down to the underlying logic
        self.configToLogic()
        # and all the way up from logic -> config -> view to make sure
        self.syncViewWithLogic()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)

        moduleBase.close(self)
        
        # get rid of our reference
        del self._imageMath

    def getInputDescriptions(self):
        return ('VTK Image Data 1', 'VTK Image Data 2')

    def setInput(self, idx, inputStream):
        if idx == 0:
            self._imageMath.SetInput1(inputStream)
        else:
            self._imageMath.SetInput2(inputStream)

    def getOutputDescriptions(self):
        return ('VTK Image Data Result',)

    def getOutput(self, idx):
        return self._imageMath.GetOutput()

    def logicToConfig(self):
        o = self._imageMath.GetOperation()
        # search for o in _operations
        for name,idx in self._operations.items():
            if idx == o:
                break

        if idx == o:
            self._config.operation = name
        else:
            # default is subtract
            self._config.operation = 'Subtract'
    
    def configToLogic(self):
        idx = self._operations[self._config.operation]
        self._imageMath.SetOperation(idx)
    
    def executeModule(self):
        self._imageMath.Update()

    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        self._viewFrame.Show(True)
        self._viewFrame.Raise()


