from moduleBase import moduleBase
from moduleMixins import vtkPipelineConfigModuleMixin
import moduleUtils
from wxPython.wx import *
import vtk

class contourFLTBase(moduleBase, vtkPipelineConfigModuleMixin):

    def __init__(self, moduleManager, contourFilterText):

        # call parent constructor
        moduleBase.__init__(self, moduleManager)

        self._contourFilterText = contourFilterText
        if contourFilterText == 'marchingCubes':
            self._contourFilter = vtk.vtkMarchingCubes()
        else: # contourFilter == 'contourFilter'
            self._contourFilter = vtk.vtkKitwareContourFilter()

        moduleUtils.setupVTKObjectProgress(self, self._contourFilter,
                                           'Extracting iso-surface')

        # now setup some defaults before our sync
        self._config.isoValue = 128;

        self._viewFrame = None
        self._createViewFrame()

        # transfer these defaults to the logic
        self.configToLogic()

        # then make sure they come all the way back up via self._config
        self.syncViewWithLogic()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        self.setInput(0, None)
        # don't forget to call the close() method of the vtkPipeline mixin
        vtkPipelineConfigModuleMixin.close(self)
        # take out our view interface
        self._viewFrame.Destroy()
        # get rid of our reference
        del self._contourFilter

    def getInputDescriptions(self):
	return ('vtkImageData',)
    

    def setInput(self, idx, inputStream):
        self._contourFilter.SetInput(inputStream)

    def getOutputDescriptions(self):
	return (self._contourFilter.GetOutput().GetClassName(),)
    

    def getOutput(self, idx):
        return self._contourFilter.GetOutput()

    def logicToConfig(self):
        self._config.isoValue = self._contourFilter.GetValue(0)

    def configToLogic(self):
        self._contourFilter.SetValue(0, self._config.isoValue)

    def viewToConfig(self):
        try:
            self._config.isoValue = float(
                self._viewFrame.isoValueText.GetValue())
        except:
            pass
        
    def configToView(self):
        self._viewFrame.isoValueText.SetValue(str(self._config.isoValue))

    def executeModule(self):
        self._contourFilter.Update()

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
        import modules.resources.python.contourFLTBaseViewFrame
        reload(modules.resources.python.contourFLTBaseViewFrame)

        self._viewFrame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager,
            modules.resources.python.contourFLTBaseViewFrame.\
            contourFLTBaseViewFrame)

        objectDict = {'contourFilter' : self._contourFilter}
        moduleUtils.createStandardObjectAndPipelineIntrospection(
            self, self._viewFrame, self._viewFrame.viewFramePanel,
            objectDict, None)

        moduleUtils.createECASButtons(
            self, self._viewFrame, self._viewFrame.viewFramePanel)
            
