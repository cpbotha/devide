from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtk

class manualTransform(scriptedConfigModuleMixin, moduleBase):
    """Manually create linear transform by entering scale factors, rotation
    angles and translations.

    Scaling is performed, then rotation, then translation.  It is often easier
    to chain manualTransform modules than performing all transformations at
    once.

    $Revision: 1.2 $
    """

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

        scriptedConfigModuleMixin.__init__(self, configList)

        self._transform = vtk.vtkTransform()
        # we want changes here to happen AFTER the transformations
        # represented by the input
        self._transform.PostMultiply()
        
        # has no progress!

        self._createWindow(
            {'Module (self)' : self,
             'vtkTransform' : self._transform})

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
        
        # get rid of our reference
        del self._transform

    def executeModule(self):
        self._transform.Update()

    def getInputDescriptions(self):
        return ()

    def setInput(self, idx, inputStream):
        raise Exception

    def getOutputDescriptions(self):
        return ('VTK Transform',)

    def getOutput(self, idx):
        return self._transform

    def logicToConfig(self):
        self._config.scale = self._transform.GetScale()
        self._config.orientation = self._transform.GetOrientation()
        self._config.translation = self._transform.GetPosition()

    
    def configToLogic(self):
        # we have to reset the transform firstn
        self._transform.Identity()
        self._transform.Scale(self._config.scale)
        self._transform.RotateX(self._config.orientation[0])
        self._transform.RotateY(self._config.orientation[1])
        self._transform.RotateZ(self._config.orientation[2])
        self._transform.Translate(self._config.translation)

        
        
