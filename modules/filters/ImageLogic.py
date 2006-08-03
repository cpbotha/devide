from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtk


class ImageLogic(scriptedConfigModuleMixin, moduleBase):


    # get these values from vtkImageMathematics.h
    _operations = ('AND', 'OR', 'XOR', 'NAND', 'NOR', 'NOT', 'NOP')
    
    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)

        self._image_logic = vtk.vtkImageLogic()
        
        moduleUtils.setupVTKObjectProgress(self, self._image_logic,
                                           'Performing image logic')
        

        self._image_cast = vtk.vtkImageCast()
        moduleUtils.setupVTKObjectProgress(
            self, self._image_cast,
            'Casting scalar type before image logic')
        

        self._config.operation = 0
        self._config.output_true_value = 1.0

        # 'choice' widget with 'base:int' type will automatically get cast
        # to index of selection that user makes.
        config_list = [
            ('Operation:', 'operation', 'base:int', 'choice',
             'The operation that should be performed.',
             tuple(self._operations)),
            ('Output true value:', 'output_true_value', 'base:float', 'text',
             'Output voxels that are TRUE will get this value.')]

        scriptedConfigModuleMixin.__init__(self, config_list)

        self._viewFrame = self._createWindow(
            {'Module (self)' : self,
             'vtkImageLogic' : self._image_logic})

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
        scriptedConfigModuleMixin.close(self)

        moduleBase.close(self)
        
        # get rid of our reference
        del self._image_logic
        del self._image_cast

    def getInputDescriptions(self):
        return ('VTK Image Data 1', 'VTK Image Data 2')

    def setInput(self, idx, inputStream):
        if idx == 0:
            self._image_logic.SetInput(0, inputStream)
        else:
            self._image_cast.SetInput(inputStream)

    def getOutputDescriptions(self):
        return ('VTK Image Data Result',)

    def getOutput(self, idx):
        return self._image_logic.GetOutput()

    def logicToConfig(self):
        self._config.operation = self._image_logic.GetOperation()
        self._config.output_true_value = \
                                       self._image_logic.GetOutputTrueValue()
    
    def configToLogic(self):
        self._image_logic.SetOperation(self._config.operation)
        self._image_logic.SetOutputTrueValue(self._config.output_true_value)
    
    def executeModule(self):
        if self._image_logic.GetInput(0) is not None:
            self._image_cast.SetOutputScalarType(
                self._image_logic.GetInput(0).GetScalarType())

        else:
            raise RuntimeError(
                'ImageLogic requires at least its first input to run.')

        if self._image_cast.GetInput() is not None:
            # both inputs, make sure image_cast is connected
            self._image_logic.SetInput(1, self._image_cast.GetOutput())
            
        else:
            # only one input, disconnect image_cast
            self._image_logic.SetInput(1, None)
            
            
        self._image_logic.Update()
        



