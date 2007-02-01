from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtk

class warpPoints(scriptedConfigModuleMixin, moduleBase):
    
    _defaultVectorsSelectionString = 'Default Active Vectors'
    _userDefinedString = 'User Defined'

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        self._config.scaleFactor = 1
        self._config.vectorsSelection = self._defaultVectorsSelectionString
        self._config.input_array_names = []
        self._config.actual_input_array = None

        configList = [
            ('Scale factor:', 'scaleFactor', 'base:float', 'text',
             'The warping will be scaled by this factor'),
            ('Vectors selection:', 'vectorsSelection', 'base:str', 'choice',
             'The attribute that will be used as vectors for the warping.',
             (self._defaultVectorsSelectionString, self._userDefinedString))]

        self._warpVector = vtk.vtkWarpVector()

        scriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
             'vtkWarpVector' : self._warpVector})
        
        moduleUtils.setupVTKObjectProgress(self, self._warpVector,
                                           'Warping points.')
        

        self.sync_module_logic_with_config()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)
        
        # get rid of our reference
        del self._warpVector

    def execute_module(self):
        self._warpVector.Update()

    def get_input_descriptions(self):
        return ('VTK points/polydata with vector attribute',)

    def set_input(self, idx, inputStream):
        self._warpVector.SetInput(inputStream)

    def get_output_descriptions(self):
        return ('Warped data',)

    def get_output(self, idx):
        # we only return something if we have something
        if self._warpVector.GetNumberOfInputConnections(0):
            return self._warpVector.GetOutput()
        else:
            return None


    def logic_to_config(self):
        self._config.scaleFactor = self._warpVector.GetScaleFactor()

        names = []
        # this is the new way of checking input connections
        if self._warpVector.GetNumberOfInputConnections(0):
            pd = self._warpVector.GetInput().GetPointData()
            if pd:
                # get a list of attribute names
                for i in range(pd.GetNumberOfArrays()):
                    names.append(pd.GetArray(i).GetName())

        self._config.input_array_names = names
                
        inf = self._warpVector.GetInputArrayInformation(0)
        vs = inf.Get(vtk.vtkDataObject.FIELD_NAME())

        self._config.actual_input_array = vs

    def config_to_view(self):
        # first get our parent mixin to do its thing
        scriptedConfigModuleMixin.config_to_view(self)

        # now we make sure that the choice is correctly filled in

        # the vector choice is the second configTuple
        choice = self._getWidget(1)

        # find out what the choices CURRENTLY are (except for the
        # default and the "user defined")
        choiceNames = []
        ccnt = choice.GetCount()
        for i in range(2,ccnt):
            choiceNames.append(choice.GetString(i))

        names = self._config.input_array_names
        if choiceNames != names:
            # this means things have changed, we have to rebuild
            # the choice
            choice.Clear()
            choice.Append(self._defaultVectorsSelectionString)
            choice.Append(self._userDefinedString)
            for name in names:
                choice.Append(name)

        if self._config.actual_input_array:
            si = choice.FindString(self._config.actual_input_array)
            if si == -1:
                # string not found, that means the user has been playing
                # behind our backs, (or he's loading a valid selection
                # from DVN) so we add it to the choice as well
                choice.Append(self._config.actual_input_array)
                choice.SetStringSelection(self._config.actual_input_array)

            else:
                choice.SetSelection(si)

        else:
            # no vector selection, so default
            choice.SetSelection(0)

    def config_to_logic(self):
        self._warpVector.SetScaleFactor(self._config.scaleFactor)

        if self._config.vectorsSelection == \
               self._defaultVectorsSelectionString:
            # default: idx, port, connection, fieldassociation (points), name
            self._warpVector.SetInputArrayToProcess(0, 0, 0, 0, None)
            
        else:
            self._warpVector.SetInputArrayToProcess(
                0, 0, 0, 0, self._config.vectorsSelection)

