import genUtils
from moduleBase import moduleBase
from moduleMixins import vtkPipelineConfigModuleMixin
import moduleUtils
from wxPython.wx import *
import vtk

class decimateFLT(moduleBase, vtkPipelineConfigModuleMixin):

    def __init__(self, moduleManager):

        # call parent constructor
        moduleBase.__init__(self, moduleManager)

        # the decimator only works on triangle data, so we make sure
        # that it only gets triangle data
        self._triFilter = vtk.vtkTriangleFilter()
        self._decimate = vtk.vtkDecimate()
        self._decimate.SetInput(self._triFilter.GetOutput())

        # following is the standard way of connecting up the dscas3 progress
        # callback to a VTK object; you should do this for all objects in
        # your module
        self._triFilter.SetProgressText('converting to triangles')
        mm = self._moduleManager
        self._triFilter.SetProgressMethod(lambda s=self, mm=mm:
                                         mm.vtk_progress_cb(s._triFilter))
        
        self._decimate.SetProgressText('decimating mesh')
        mm = self._moduleManager
        self._decimate.SetProgressMethod(lambda s=self, mm=mm:
                                         mm.vtk_progress_cb(s._decimate))

        # now setup some defaults before our sync
        self._config.targetReduction = self._decimate.GetTargetReduction()

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
        del self._decimate
        del self._triFilter

    def getInputDescriptions(self):
	return ('vtkPolyData',)
    
    def setInput(self, idx, inputStream):
        self._triFilter.SetInput(inputStream)
    
    def getOutputDescriptions(self):
	return (self._decimate.GetOutput().GetClassName(),)
    
    def getOutput(self, idx):
        return self._decimate.GetOutput()

    def logicToConfig(self):
        self._config.targetReduction = self._decimate.GetTargetReduction()

    def configToLogic(self):
        self._decimate.SetTargetReduction(self._config.targetReduction)

    def viewToConfig(self):
        self._config.targetReduction = self._viewFrame.targetReductionSlider.\
                                       GetValue() / 100.0

    def configToView(self):
        self._viewFrame.targetReductionSlider.SetValue(
            self._config.targetReduction * 100.0)

    def executeModule(self):
        # get the filter doing its thing
        self._decimate.Update()

        # tell the vtk log file window to poll the file; if the file has
        # changed, i.e. vtk has written some errors, the log window will
        # pop up.  you should do this in all your modules right after you
        # caused some VTK processing which might have resulted in VTK
        # outputting to the error log
        self._moduleManager.vtk_poll_error()

    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        if not self._viewFrame.Show(true):
            self._viewFrame.Raise()

    def _createViewFrame(self):

        # import the viewFrame (created with wxGlade)
        import modules.resources.python.decimateFLTViewFrame
        reload(modules.resources.python.decimateFLTViewFrame)

        # find our parent window and instantiate the frame
        pw = self._moduleManager.get_module_view_parent_window()
        self._viewFrame = modules.resources.python.decimateFLTViewFrame.\
                          decimateFLTViewFrame(pw, -1, 'dummy')

        # make sure that a close of that window does the right thing
        EVT_CLOSE(self._viewFrame,
                  lambda e, s=self: s._viewFrame.Show(false))

        # default binding for the buttons at the bottom
        moduleUtils.bindCSAEO(self, self._viewFrame)        

        # and now the standard examine object/pipeline stuff
        EVT_CHOICE(self._viewFrame, self._viewFrame.objectChoiceId,
                   self.vtkObjectChoiceCallback)
        EVT_BUTTON(self._viewFrame, self._viewFrame.pipelineButtonId,
                   self.vtkPipelineCallback)
        
        
    def vtkObjectChoiceCallback(self, event):
        choice = self._viewFrame.objectChoice.GetStringSelection()
        if choice == 'vtkDecimate':
            self.vtkObjectConfigure(self._viewFrame, None,
                                    self._decimate)
            
        elif choice == 'vtkTriangleFilter':
            self.vtkObjectConfigure(self._viewFrame, None,
                                    self._triFilter)

        else:
            genUtils.wxLogError('decimateFLT.py: This should not happen!')
            

    def vtkPipelineCallback(self, event):
        # move this to module utils too, or to base...
        self.vtkPipelineConfigure(self._viewFrame, None,
                                  (self._decimate,))
