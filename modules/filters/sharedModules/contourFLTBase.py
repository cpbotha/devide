from module_base import ModuleBase
from moduleMixins import vtkPipelineConfigModuleMixin
import module_utils
import vtk

class contourFLTBase(ModuleBase, vtkPipelineConfigModuleMixin):

    def __init__(self, module_manager, contourFilterText):

        # call parent constructor
        ModuleBase.__init__(self, module_manager)

        self._contourFilterText = contourFilterText
        if contourFilterText == 'marchingCubes':
            self._contourFilter = vtk.vtkMarchingCubes()
        else: # contourFilter == 'contourFilter'
            self._contourFilter = vtk.vtkContourFilter()

        module_utils.setupVTKObjectProgress(self, self._contourFilter,
                                           'Extracting iso-surface')

        # now setup some defaults before our sync
        self._config.isoValue = 128;

        self._viewFrame = None
        self._createViewFrame()

        # transfer these defaults to the logic
        self.config_to_logic()

        # then make sure they come all the way back up via self._config
        self.logic_to_config()
        self.config_to_view()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        self.set_input(0, None)
        # don't forget to call the close() method of the vtkPipeline mixin
        vtkPipelineConfigModuleMixin.close(self)
        # take out our view interface
        self._viewFrame.Destroy()
        # get rid of our reference
        del self._contourFilter

    def get_input_descriptions(self):
	return ('vtkImageData',)
    

    def set_input(self, idx, inputStream):
        self._contourFilter.SetInput(inputStream)

    def get_output_descriptions(self):
	return (self._contourFilter.GetOutput().GetClassName(),)
    

    def get_output(self, idx):
        return self._contourFilter.GetOutput()

    def logic_to_config(self):
        self._config.isoValue = self._contourFilter.GetValue(0)

    def config_to_logic(self):
        self._contourFilter.SetValue(0, self._config.isoValue)

    def view_to_config(self):
        try:
            self._config.isoValue = float(
                self._viewFrame.isoValueText.GetValue())
        except:
            pass
        
    def config_to_view(self):
        self._viewFrame.isoValueText.SetValue(str(self._config.isoValue))

    def execute_module(self):
        self._contourFilter.Update()

    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()

    def _createViewFrame(self):

        # import the viewFrame (created with wxGlade)
        import modules.Filters.resources.python.contourFLTBaseViewFrame
        reload(modules.Filters.resources.python.contourFLTBaseViewFrame)

        self._viewFrame = module_utils.instantiateModuleViewFrame(
            self, self._module_manager,
            modules.Filters.resources.python.contourFLTBaseViewFrame.\
            contourFLTBaseViewFrame)

        objectDict = {'contourFilter' : self._contourFilter}
        module_utils.createStandardObjectAndPipelineIntrospection(
            self, self._viewFrame, self._viewFrame.viewFramePanel,
            objectDict, None)

        module_utils.createECASButtons(
            self, self._viewFrame, self._viewFrame.viewFramePanel)
            
