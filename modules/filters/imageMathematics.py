import genUtils
from module_base import ModuleBase
from moduleMixins import ScriptedConfigModuleMixin
import module_utils
import vtk

class imageMathematics(ScriptedConfigModuleMixin, ModuleBase):

    # get these values from vtkImageMathematics.h
    _operations = {'Add' : 0,
                   'Subtract' : 1,
                   'Maximum' : 13,
                   'Add constant C' : 17}
    
    def __init__(self, module_manager):
        # initialise our base class
        ModuleBase.__init__(self, module_manager)


        self._imageMath = vtk.vtkImageMathematics()
        self._imageMath.SetInput1(None)
        self._imageMath.SetInput2(None)
        
        module_utils.setupVTKObjectProgress(self, self._imageMath,
                                           'Performing image math')
        
                                           
        self._config.operation = 'Subtract'
        self._config.constantC = 0.0
        self._config.constantK = 1.0


        configList = [
            ('Operation:', 'operation', 'base:str', 'choice',
             'The operation that should be performed.',
             tuple(self._operations.keys())),
            ('Constant C:', 'constantC', 'base:float', 'text',
             'The constant C used in some operations.'),
            ('Constant K:', 'constantK', 'base:float', 'text',
             'The constant C used in some operations.')]

        ScriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
             'vtkImageMathematics' : self._imageMath})

        self.sync_module_logic_with_config()
        
    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        ScriptedConfigModuleMixin.close(self)

        ModuleBase.close(self)
        
        # get rid of our reference
        del self._imageMath

    def get_input_descriptions(self):
        return ('VTK Image Data 1', 'VTK Image Data 2')

    def set_input(self, idx, inputStream):
        if idx == 0:
            self._imageMath.SetInput1(inputStream)
        else:
            self._imageMath.SetInput2(inputStream)

    def get_output_descriptions(self):
        return ('VTK Image Data Result',)

    def get_output(self, idx):
        return self._imageMath.GetOutput()

    def logic_to_config(self):
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

        self._config.constantC = self._imageMath.GetConstantC()
        self._config.constantK = self._imageMath.GetConstantK()
    
    def config_to_logic(self):
        idx = self._operations[self._config.operation]
        self._imageMath.SetOperation(idx)

        self._imageMath.SetConstantC(self._config.constantC)
        self._imageMath.SetConstantK(self._config.constantK)
    
    def execute_module(self):
        self._imageMath.Update()
        

    def streaming_execute_module(self):
        self._imageMath.Update()


