import genUtils
from moduleBase import moduleBase
from moduleMixins import vtkPipelineConfigModuleMixin
import moduleUtils
from wxPython.wx import *
import vtk

class marchingCubesFLT(moduleBase, vtkPipelineConfigModuleMixin):

    def __init__(self, moduleManager):

        # call parent constructor
        moduleBase.__init__(self, moduleManager)

        self._marchingCubes = vtk.vtkMarchingCubes()

        # now setup some defaults before our sync
        self._config.isoValue = 128;
        self._config.rtu = 0

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
        # don't forget to call the close() method of the vtkPipeline mixin
        vtkPipelineConfigModuleMixin.close(self)
        # take out our view interface
        self._viewFrame.Destroy()
        # get rid of our reference
        del self._marchingCubes

    def getInputDescriptions(self):
	return ('vtkImageData',)
    
    def setInput(self, idx, inputStream):
        self._marchingCubes.SetInput(inputStream)
        if not inputStream is None:
            # get scalar bounds
            minv, maxv = inputStream.GetScalarRange()
            self._viewFrame.isoValueSlider.SetRange(minv, maxv)
    
    def getOutputDescriptions(self):
	return (self._marchingCubes.GetOutput().GetClassName(),)
    
    def getOutput(self, idx):
        return self._marchingCubes.GetOutput()

    def logicToConfig(self):
        self._config.isoValue = self._marchingCubes.GetValue(0)

    def configToLogic(self):
        self._marchingCubes.SetValue(0, self._config.isoValue)

    def viewToConfig(self):
        self._config.isoValue = self._viewFrame.isoValueSlider.GetValue()
        self._config.rtu = self._viewFrame.realtimeUpdateCheckBox.GetValue()

    def configToView(self):
        self._viewFrame.isoValueSlider.SetValue(self._config.isoValue)
        self._viewFrame.realtimeUpdateCheckBox.SetValue(self._config.rtu)

    def executeModule(self):
        # following is the standard way of connecting up the dscas3 progress
        # callback to a VTK object; you should do this for all objects in
        # your module - you could do this in __init__ as well, it seems
        # neater here though
        self._marchingCubes.SetProgressText('Performing marching cubes')
        mm = self._moduleManager
        self._marchingCubes.SetProgressMethod(lambda s=self, mm=mm:
                                               mm.vtk_progress_cb(
            s._marchingCubes))
        
        self._marchingCubes.Update()

        # tell the vtk log file window to poll the file; if the file has
        # changed, i.e. vtk has written some errors, the log window will
        # pop up.  you should do this in all your modules right after you
        # caused some VTK processing which might have resulted in VTK
        # outputting to the error log
        self._moduleManager.vtk_poll_error()

        mm.setProgress(100, 'DONE performing marching cubes')

    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        if not self._viewFrame.Show(true):
            self._viewFrame.Raise()

    def _createViewFrame(self):

        # import the viewFrame (created with wxGlade)
        import modules.resources.python.marchingCubesFLTViewFrame
        reload(modules.resources.python.marchingCubesFLTViewFrame)

        # find our parent window and instantiate the frame
        pw = self._moduleManager.get_module_view_parent_window()
        self._viewFrame = modules.resources.python.marchingCubesFLTViewFrame.\
                          marchingCubesFLTViewFrame(pw, -1, 'dummy')

        # make sure that a close of that window does the right thing
        EVT_CLOSE(self._viewFrame,
                  lambda e, s=self: s._viewFrame.Show(false))

        # default binding for the buttons at the bottom
        moduleUtils.bindCSAEO(self, self._viewFrame)        

        # connect slider to its callback for instant processing
        EVT_SCROLL(self._viewFrame.isoValueSlider,
                   self._sliderCallback())

        # the checkbox should directly modify its own bit of the self._config
        EVT_CHECKBOX(self._viewFrame,
                     self._viewFrame.realtimeUpdateCheckBoxId,
                     self._realtimeUpdateCheckBoxCallback)

        # and now the standard examine object/pipeline stuff
        EVT_CHOICE(self._viewFrame, self._viewFrame.objectChoiceId,
                   self.vtkObjectChoiceCallback)
        EVT_BUTTON(self._viewFrame, self._viewFrame.pipelineButtonId,
                   self.vtkPipelineCallback)
        
        

    def _sliderCallback(self):
        if self._config.rtu:
            self.applyViewToLogic()
            self.executeModule()

    def _realtimeUpdateCheckBoxCallback(self, event):
        self._config.rtu = self._viewFrame.realtimeUpdateCheckBox.GetValue()
        
    def vtkObjectChoiceCallback(self, event):
        self.vtkObjectConfigure(self._viewFrame, None,
                                self._marchingCubes)

    def vtkPipelineCallback(self, event):
        # move this to module utils too, or to base...
        self.vtkPipelineConfigure(self._viewFrame, None,
                                  (self._marchingCubes,))
