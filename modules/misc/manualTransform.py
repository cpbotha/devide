from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtk

class manualTransform(scriptedConfigModuleMixin, moduleBase):

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        self._config.scale = (1.0, 1.0, 1.0)
        self._config.orientation = (0.0, 0.0, 0.0)
        self._config.translation = (0.0, 0.0, 0.0)

        configList = [
            ('Scaling:', 'scale', 'tuple:float,3', 'tupleText',
             'Scale factor in the x, y and z directions in world units.'),
            ('Orientation:', 'orientation', 'tuple:float,3', 'tupleText',
             'Rotation, in order, around the x, the new y and the new z axes '
             'in degrees.'),            
            ('Translation:', 'translation', 'tuple:float,3', 'tupleText',
             'Translation in the x,y,z directions.')]



        self._transform = vtk.vtkTransform()
        # we want changes here to happen AFTER the transformations
        # represented by the input
        self._transform.PostMultiply()
        
        # has no progress!

        scriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
             'vtkTransform' : self._transform})
            
        self.sync_module_logic_with_config()
        
    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)
        
        # get rid of our reference
        del self._transform

    def execute_module(self):
        self._transform.Update()

    def get_input_descriptions(self):
        return ()

    def set_input(self, idx, inputStream):
        raise Exception

    def get_output_descriptions(self):
        return ('VTK Transform',)

    def get_output(self, idx):
        return self._transform

    def logic_to_config(self):
        self._config.scale = self._transform.GetScale()
        self._config.orientation = self._transform.GetOrientation()
        self._config.translation = self._transform.GetPosition()

    
    def config_to_logic(self):
        # we have to reset the transform firstn
        self._transform.Identity()
        self._transform.Scale(self._config.scale)
        self._transform.RotateX(self._config.orientation[0])
        self._transform.RotateY(self._config.orientation[1])
        self._transform.RotateZ(self._config.orientation[2])
        self._transform.Translate(self._config.translation)

        
        
