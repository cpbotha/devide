# imageGaussianSmooth copyright (c) 2003 by Charl P. Botha cpbotha@ieee.org
# $Id$
# performs image smoothing by convolving with a Gaussian

import gen_utils
from module_base import ModuleBase
from module_mixins import IntrospectModuleMixin
import module_utils
import vtk

class imageGaussianSmooth(IntrospectModuleMixin, ModuleBase):

    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        self._imageGaussianSmooth = vtk.vtkImageGaussianSmooth()

        module_utils.setupVTKObjectProgress(self, self._imageGaussianSmooth,
                                           'Smoothing image with Gaussian')
        

        self._config.standardDeviation = (2.0, 2.0, 2.0)
        self._config.radiusCutoff = (1.5, 1.5, 1.5)

        self._view_frame = None


        self._module_manager.sync_module_logic_with_config(self)

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        self.set_input(0, None)
        # don't forget to call the close() method of the vtkPipeline mixin
        IntrospectModuleMixin.close(self)
        # take out our view interface
        if self._view_frame is not None:
            self._view_frame.Destroy()
            
        # get rid of our reference
        del self._imageGaussianSmooth
        # and finally call our base dtor
        ModuleBase.close(self)
        
    def get_input_descriptions(self):
        return ('vtkImageData',)

    def set_input(self, idx, inputStream):
        self._imageGaussianSmooth.SetInput(inputStream)

    def get_output_descriptions(self):
        return (self._imageGaussianSmooth.GetOutput().GetClassName(),)

    def get_output(self, idx):
        return self._imageGaussianSmooth.GetOutput()

    def logic_to_config(self):
        self._config.standardDeviation = self._imageGaussianSmooth.\
                                         GetStandardDeviations()
        self._config.radiusCutoff = self._imageGaussianSmooth.\
                                    GetRadiusFactors()

    def config_to_logic(self):
        self._imageGaussianSmooth.SetStandardDeviations(
            self._config.standardDeviation)
        self._imageGaussianSmooth.SetRadiusFactors(
            self._config.radiusCutoff)

    def view_to_config(self):
        # continue with textToTuple in gen_utils
        stdText = self._view_frame.stdTextCtrl.GetValue()
        self._config.standardDeviation = gen_utils.textToTypeTuple(
            stdText, self._config.standardDeviation, 3, float)
        
        cutoffText = self._view_frame.radiusCutoffTextCtrl.GetValue()
        self._config.radiusCutoff = gen_utils.textToTypeTuple(
            cutoffText, self._config.radiusCutoff, 3, float)

    def config_to_view(self):
        stdText = '(%.2f, %.2f, %.2f)' % self._config.standardDeviation
        self._view_frame.stdTextCtrl.SetValue(stdText)

        cutoffText = '(%.2f, %.2f, %.2f)' % self._config.radiusCutoff
        self._view_frame.radiusCutoffTextCtrl.SetValue(cutoffText)

    def execute_module(self):
        self._imageGaussianSmooth.Update()
        

    def view(self, parent_window=None):
        if self._view_frame is None:
            self._createViewFrame()
            # the logic is the bottom line in this case
            self._module_manager.sync_module_view_with_logic(self)
            
        # if the window was visible already. just raise it
        self._view_frame.Show(True)
        self._view_frame.Raise()

    def _createViewFrame(self):
        self._module_manager.import_reload(
            'modules.filters.resources.python.imageGaussianSmoothViewFrame')
        import modules.filters.resources.python.imageGaussianSmoothViewFrame

        self._view_frame = module_utils.instantiateModuleViewFrame(
            self, self._module_manager,
            modules.filters.resources.python.imageGaussianSmoothViewFrame.\
            imageGaussianSmoothViewFrame)

        objectDict = {'vtkImageGaussianSmooth' : self._imageGaussianSmooth}
        module_utils.createStandardObjectAndPipelineIntrospection(
            self, self._view_frame, self._view_frame.viewFramePanel,
            objectDict, None)

        module_utils.createECASButtons(self, self._view_frame,
                                      self._view_frame.viewFramePanel)

