import genUtils
from moduleBase import moduleBase
from moduleMixins import vtkPipelineConfigModuleMixin
import moduleUtils
from wxPython.wx import *
import vtk

class doubleThresholdFLT(moduleBase,
                         vtkPipelineConfigModuleMixin):

    def __init__(self, moduleManager):

        # call parent constructor
        moduleBase.__init__(self, moduleManager)

        self._imageThreshold = vtk.vtkImageThreshold()

        # following is the standard way of connecting up the dscas3 progress
        # callback to a VTK object; you should do this for all objects in
        # your module - you could do this in __init__ as well, it seems
        # neater here though
#         self._imageThreshold.SetProgressText('Thresholding data')
#         mm = self._moduleManager
#         self._imageThreshold.SetProgressMethod(lambda s=self, mm=mm:
#                                                mm.vtk_progress_cb(
#             s._imageThreshold))
        

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

        self._viewFrame = None
        self._createViewFrame()

        # now setup some defaults before our sync
        self._config.lt = 1250
        self._config.ut = 2500
        self._config.rtu = 1
        self._config.ri = 1
        self._config.iv = 1
        self._config.ro = 1
        self._config.ov = 0
        self._config.os = self._imageThreshold.GetOutputScalarType()

        # transfer these defaults to the logic
        self.configToLogic()

        # then make sure they come all the way back up via self._config
        self.syncViewWithLogic()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        self.setInput(0, None)
        # close down the vtkPipeline stuff
        vtkPipelineConfigModuleMixin.close(self)
        # take out our view interface
        self._viewFrame.Destroy()
        # get rid of our reference
        del self._imageThreshold

    def getInputDescriptions(self):
	return ('vtkImageData',)
    

    def setInput(self, idx, inputStream):
        self._imageThreshold.SetInput(inputStream)
        if not inputStream is None:
            # get scalar bounds
            minv, maxv = inputStream.GetScalarRange()

    def getOutputDescriptions(self):
	return ('vtkImageData',)
    

    def getOutput(self, idx):
        return self._imageThreshold.GetOutput()

    def logicToConfig(self):
        self._config.lt = self._imageThreshold.GetLowerThreshold()
        self._config.ut = self._imageThreshold.GetUpperThreshold()
        self._config.ri = self._imageThreshold.GetReplaceIn()
        self._config.iv = self._imageThreshold.GetInValue()
        self._config.ro = self._imageThreshold.GetReplaceOut()
        self._config.ov = self._imageThreshold.GetOutValue()
        self._config.os = self._imageThreshold.GetOutputScalarType()

    def configToLogic(self):
        self._imageThreshold.ThresholdBetween(self._config.lt, self._config.ut)
        # SetInValue HAS to be called before SetReplaceIn(), as SetInValue()
        # always toggles SetReplaceIn() to ON
        self._imageThreshold.SetInValue(self._config.iv)        
        self._imageThreshold.SetReplaceIn(self._config.ri)
        # SetOutValue HAS to be called before SetReplaceOut(), same reason
        # as above
        self._imageThreshold.SetOutValue(self._config.ov)
        self._imageThreshold.SetReplaceOut(self._config.ro)
        self._imageThreshold.SetOutputScalarType(self._config.os)

    def viewToConfig(self):
        self._config.lt = self._sanitiseThresholdTexts(0)
        self._config.ut = self._sanitiseThresholdTexts(1)
        self._config.rtu = self._viewFrame.realtimeUpdateCheckbox.GetValue()
        self._config.ri = self._viewFrame.replaceInCheckBox.GetValue()
        self._config.iv = float(self._viewFrame.replaceInText.GetValue())
        self._config.ro = self._viewFrame.replaceOutCheckBox.GetValue()
        self._config.ov = float(self._viewFrame.replaceOutText.GetValue())

        ocString = self._viewFrame.outputDataTypeChoice.GetStringSelection()
        if len(ocString) == 0:
            genUtils.logError("Impossible error with outputType choice in "
                              "doubleThresholdFLT.py.  Picking sane default.")
            # set to last string in list, should be default
            ocString = self._outputTypes.keys()[-1]

        try:
            symbolicOutputType = self._outputTypes[ocString]
        except KeyError:
            genUtils.logError("Impossible error with ocString in "
                              "doubleThresholdFLT.py.  Picking sane default.")
            # set to last string in list, should be default
            symbolicOutputType = self._outputTypes.values()[-1]

        if symbolicOutputType == -1:
            self._config.os = -1
        else:
            try:
                self._config.os = getattr(vtk, symbolicOutputType)
            except AttributeError:
                genUtils.logError("Impossible error with symbolicOutputType "
                                  "in doubleThresholdFLT.py.  Picking sane "
                                  "default.")
                self._config.os = -1

    def configToView(self):
        self._viewFrame.lowerThresholdText.SetValue("%.2f" % (self._config.lt))
        self._viewFrame.upperThresholdText.SetValue("%.2f" % (self._config.ut))
        self._viewFrame.realtimeUpdateCheckbox.SetValue(self._config.rtu)
        self._viewFrame.replaceInCheckBox.SetValue(self._config.ri)
        self._viewFrame.replaceInText.SetValue(str(self._config.iv))
        self._viewFrame.replaceOutCheckBox.SetValue(self._config.ro)
        self._viewFrame.replaceOutText.SetValue(str(self._config.ov))

        for key in self._outputTypes.keys():
            symbolicOutputType = self._outputTypes[key]
            if hasattr(vtk, str(symbolicOutputType)):
                numericOutputType = getattr(vtk, symbolicOutputType)
            else:
                numericOutputType = -1
                
            if self._config.os == numericOutputType:
                break

        self._viewFrame.outputDataTypeChoice.SetStringSelection(key)

    def executeModule(self):
        # don't ask... we have to call Update() twice here, I _think_
        # due to weirdness in vtkImageThreshold() that I haven't been
        # able to track down.  If update is called only once, a
        # directly connected slice3dVWR will Render() but only show
        # the PREVIOUS output of the _imageThreshold.  My current
        # hypothesis is that this is due to the ThreadedExecute
        # employed by vtkImageThreshold, i.e. Update() is
        # non-blocking.  This hypothesis is of course still full of
        # holes. :)
        self._imageThreshold.Update()
        #self._imageThreshold.Update()

        # fixed it now by adding observer to EndEvent of source of data
        # input in sliceviewer

        # tell the vtk log file window to poll the file; if the file has
        # changed, i.e. vtk has written some errors, the log window will
        # pop up.  you should do this in all your modules right after you
        # caused some VTK processing which might have resulted in VTK
        # outputting to the error log
        self._moduleManager.vtk_poll_error()

    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()

    def _createViewFrame(self):

        # import the viewFrame (created with wxGlade)
        import modules.resources.python.doubleThresholdFLTFrame
        reload(modules.resources.python.doubleThresholdFLTFrame)

        # find our parent window and instantiate the frame
        pw = self._moduleManager.get_module_view_parent_window()
        self._viewFrame = modules.resources.python.doubleThresholdFLTFrame.\
                          doubleThresholdFLTFrame(pw, -1, 'dummy')

        # make sure that a close of that window does the right thing
        EVT_CLOSE(self._viewFrame,
                  lambda e, s=self: s._viewFrame.Show(false))

        # default binding for the buttons at the bottom
        moduleUtils.bindCSAEO(self, self._viewFrame)        

        # finish setting up the output datatype choice
        self._viewFrame.outputDataTypeChoice.Clear()
        for aType in self._outputTypes.keys():
            self._viewFrame.outputDataTypeChoice.Append(aType)

        EVT_TEXT_ENTER(self._viewFrame,
                       self._viewFrame.lowerThresholdTextId,
                       lambda e, s=self: s._threshTextCallback(0))

        EVT_TEXT_ENTER(self._viewFrame,
                       self._viewFrame.upperThresholdTextId,
                       lambda e, s=self: s._threshTextCallback(1))

        EVT_CHECKBOX(self._viewFrame,
                     self._viewFrame.realtimeUpdateCheckboxId,
                     self._realtimeUpdateCheckboxCallback)

        # and now the standard examine object/pipeline stuff
        EVT_CHOICE(self._viewFrame, self._viewFrame.objectChoiceId,
                   self.vtk_object_choice_cb)
        EVT_BUTTON(self._viewFrame, self._viewFrame.pipelineButtonId,
                   self.vtk_pipeline_cb)
        
    def _sanitiseThresholdTexts(self, whichText):
        if whichText == 0:
            try:
                lower = float(self._viewFrame.lowerThresholdText.GetValue())
            except ValueError:
                # this means that the user did something stupid, so we
                # restore the value to what's in our config
                self._viewFrame.lowerThresholdText.SetValue(str(
                    self._config.lt))
                
                return self._config.lt
                
            # lower is the new value...
            upper = float(self._viewFrame.upperThresholdText.GetValue())
            if lower > upper:
                lower = upper
                self._viewFrame.lowerThresholdText.SetValue(str(lower))

            return lower

        else:
            try:
                upper = float(self._viewFrame.upperThresholdText.GetValue())
            except ValueError:
                # this means that the user did something stupid, so we
                # restore the value to what's in our config
                self._viewFrame.upperThresholdText.SetValue(str(
                    self._config.ut))
                
                return self._config.ut

            # upper is the new value
            lower = float(self._viewFrame.lowerThresholdText.GetValue())
            if upper < lower:
                upper = lower
                self._viewFrame.upperThresholdText.SetValue(str(upper))

            return upper
        

    def _threshTextCallback(self, whichText):
        self._sanitiseThresholdTexts(whichText)

        if self._config.rtu:
            self.applyViewToLogic()
            self.executeModule()

    def _realtimeUpdateCheckboxCallback(self, event):
        self._config.rtu = self._viewFrame.realtimeUpdateCheckbox.GetValue()
        

    def vtk_object_choice_cb(self, event):
        self.vtkObjectConfigure(self._viewFrame, None,
                                self._imageThreshold)

    def vtk_pipeline_cb(self, event):
        # move this to module utils too, or to base...
        self.vtkPipelineConfigure(self._viewFrame, None,
                                  (self._imageThreshold,))
