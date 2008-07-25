import genUtils
from module_base import ModuleBase
from moduleMixins import introspectModuleMixin
import moduleUtils
import vtk

class doubleThreshold(introspectModuleMixin, ModuleBase):

    def __init__(self, module_manager):

        # call parent constructor
        ModuleBase.__init__(self, module_manager)

        self._imageThreshold = vtk.vtkImageThreshold()

        moduleUtils.setupVTKObjectProgress(self, self._imageThreshold,
                                           'Thresholding data')
        

        self._outputTypes = {'Double': 'VTK_DOUBLE',
                             'Float' : 'VTK_FLOAT',
                             'Long'  : 'VTK_LONG',
                             'Unsigned Long' : 'VTK_UNSIGNED_LONG',
                             'Integer' : 'VTK_INT',
                             'Unsigned Integer' : 'VTK_UNSIGNED_INT',
                             'Short' : 'VTK_SHORT',
                             'Unsigned Short' : 'VTK_UNSIGNED_SHORT',
                             'Char' : 'VTK_CHAR',
                             'Unsigned Char' : 'VTK_UNSIGNED_CHAR',
                             'Same as input' : -1}

        self._view_frame = None

        # now setup some defaults before our sync
        self._config.lowerThreshold = 1250
        self._config.upperThreshold = 2500
        #self._config.rtu = 1
        self._config.replaceIn = 1
        self._config.inValue = 1
        self._config.replaceOut = 1
        self._config.outValue = 0
        self._config.outputScalarType = self._imageThreshold.GetOutputScalarType()

        self.sync_module_logic_with_config()
        
    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        self.set_input(0, None)
        # close down the vtkPipeline stuff
        introspectModuleMixin.close(self)
        # take out our view interface
        if self._view_frame is not None:
            self._view_frame.Destroy()
            
        # get rid of our reference
        del self._imageThreshold

    def get_input_descriptions(self):
	return ('vtkImageData',)
    

    def set_input(self, idx, inputStream):
        self._imageThreshold.SetInput(inputStream)
        if not inputStream is None:
            # get scalar bounds
            minv, maxv = inputStream.GetScalarRange()

    def get_output_descriptions(self):
	return ('Thresholded data (vtkImageData)',)
    

    def get_output(self, idx):
        return self._imageThreshold.GetOutput()

    def logic_to_config(self):
        self._config.lowerThreshold = self._imageThreshold.GetLowerThreshold()
        self._config.upperThreshold = self._imageThreshold.GetUpperThreshold()
        self._config.replaceIn = self._imageThreshold.GetReplaceIn()
        self._config.inValue = self._imageThreshold.GetInValue()
        self._config.replaceOut = self._imageThreshold.GetReplaceOut()
        self._config.outValue = self._imageThreshold.GetOutValue()
        self._config.outputScalarType = self._imageThreshold.GetOutputScalarType()

    def config_to_logic(self):
        self._imageThreshold.ThresholdBetween(self._config.lowerThreshold, self._config.upperThreshold)
        # SetInValue HAS to be called before SetReplaceIn(), as SetInValue()
        # always toggles SetReplaceIn() to ON
        self._imageThreshold.SetInValue(self._config.inValue)        
        self._imageThreshold.SetReplaceIn(self._config.replaceIn)
        # SetOutValue HAS to be called before SetReplaceOut(), same reason
        # as above
        self._imageThreshold.SetOutValue(self._config.outValue)
        self._imageThreshold.SetReplaceOut(self._config.replaceOut)
        self._imageThreshold.SetOutputScalarType(self._config.outputScalarType)

    def view_to_config(self):
        self._config.lowerThreshold = self._sanitiseThresholdTexts(0)
        self._config.upperThreshold = self._sanitiseThresholdTexts(1)
        self._config.replaceIn = self._view_frame.replaceInCheckBox.GetValue()
        self._config.inValue = float(self._view_frame.replaceInText.GetValue())
        self._config.replaceOut = self._view_frame.replaceOutCheckBox.GetValue()
        self._config.outValue = float(self._view_frame.replaceOutText.GetValue())

        ocString = self._view_frame.outputDataTypeChoice.GetStringSelection()
        if len(ocString) == 0:
            self._module_manager.log_error(
                "Impossible error with outputType choice in "
                "doubleThresholdFLT.py.  Picking sane default.")
            # set to last string in list, should be default
            ocString = self._outputTypes.keys()[-1]

        try:
            symbolicOutputType = self._outputTypes[ocString]
        except KeyError:
            self._module_manager.log_error(
                "Impossible error with ocString in "
                "doubleThresholdFLT.py.  Picking sane default.")
            # set to last string in list, should be default
            symbolicOutputType = self._outputTypes.values()[-1]

        if symbolicOutputType == -1:
            self._config.outputScalarType = -1
        else:
            try:
                self._config.outputScalarType = getattr(vtk, symbolicOutputType)
            except AttributeError:
                self._module_manager.log_error(
                    "Impossible error with symbolicOutputType "
                    "in doubleThresholdFLT.py.  Picking sane "
                    "default.")
                self._config.outputScalarType = -1

    def config_to_view(self):
        self._view_frame.lowerThresholdText.SetValue("%.2f" % (self._config.lowerThreshold))
        self._view_frame.upperThresholdText.SetValue("%.2f" % (self._config.upperThreshold))
        self._view_frame.replaceInCheckBox.SetValue(self._config.replaceIn)
        self._view_frame.replaceInText.SetValue(str(self._config.inValue))
        self._view_frame.replaceOutCheckBox.SetValue(self._config.replaceOut)
        self._view_frame.replaceOutText.SetValue(str(self._config.outValue))

        for key in self._outputTypes.keys():
            symbolicOutputType = self._outputTypes[key]
            if hasattr(vtk, str(symbolicOutputType)):
                numericOutputType = getattr(vtk, symbolicOutputType)
            else:
                numericOutputType = -1
                
            if self._config.outputScalarType == numericOutputType:
                break

        self._view_frame.outputDataTypeChoice.SetStringSelection(key)

    def execute_module(self):
        self._imageThreshold.Update()

    def streaming_execute_module(self):
        self._imageThreshold.Update()

    def view(self, parent_window=None):
        if self._view_frame is None:
            self._createViewFrame()
            self.sync_module_view_with_logic()
        
        # if the window was visible already. just raise it
        self._view_frame.Show(True)
        self._view_frame.Raise()

    def _createViewFrame(self):

        # import the viewFrame (created with wxGlade)
        import modules.filters.resources.python.doubleThresholdFLTFrame
        reload(modules.filters.resources.python.doubleThresholdFLTFrame)

        self._view_frame = moduleUtils.instantiateModuleViewFrame(
            self, self._module_manager,
            modules.filters.resources.python.doubleThresholdFLTFrame.\
            doubleThresholdFLTFrame)

        objectDict = {'imageThreshold' : self._imageThreshold,
                      'module (self)' : self}
        moduleUtils.createStandardObjectAndPipelineIntrospection(
            self, self._view_frame, self._view_frame.viewFramePanel,
            objectDict, None)

        moduleUtils.createECASButtons(self, self._view_frame,
                                      self._view_frame.viewFramePanel)

        # finish setting up the output datatype choice
        self._view_frame.outputDataTypeChoice.Clear()
        for aType in self._outputTypes.keys():
            self._view_frame.outputDataTypeChoice.Append(aType)    

    def _sanitiseThresholdTexts(self, whichText):
        if whichText == 0:
            try:
                lower = float(self._view_frame.lowerThresholdText.GetValue())
            except ValueError:
                # this means that the user did something stupid, so we
                # restore the value to what's in our config
                self._view_frame.lowerThresholdText.SetValue(str(
                    self._config.lowerThreshold))
                
                return self._config.lowerThreshold
                
            # lower is the new value...
            upper = float(self._view_frame.upperThresholdText.GetValue())
            if lower > upper:
                lower = upper
                self._view_frame.lowerThresholdText.SetValue(str(lower))

            return lower

        else:
            try:
                upper = float(self._view_frame.upperThresholdText.GetValue())
            except ValueError:
                # this means that the user did something stupid, so we
                # restore the value to what's in our config
                self._view_frame.upperThresholdText.SetValue(str(
                    self._config.upperThreshold))
                
                return self._config.upperThreshold

            # upper is the new value
            lower = float(self._view_frame.lowerThresholdText.GetValue())
            if upper < lower:
                upper = lower
                self._view_frame.upperThresholdText.SetValue(str(upper))

            return upper
