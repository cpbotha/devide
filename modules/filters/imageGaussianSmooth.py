# imageGaussianSmooth copyright (c) 2003 by Charl P. Botha cpbotha@ieee.org
# $Id$
# performs image smoothing by convolving with a Gaussian

import genUtils
from moduleBase import moduleBase
from moduleMixins import introspectModuleMixin
import moduleUtils
import vtk

class imageGaussianSmooth(introspectModuleMixin, moduleBase):

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        self._imageGaussianSmooth = vtk.vtkImageGaussianSmooth()

        moduleUtils.setupVTKObjectProgress(self, self._imageGaussianSmooth,
                                           'Smoothing image with Gaussian')
        

        self._config.standardDeviation = (2.0, 2.0, 2.0)
        self._config.radiusCutoff = (1.5, 1.5, 1.5)

        self._view_frame = None


        self._moduleManager.sync_module_logic_with_config(self)

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        self.set_input(0, None)
        # don't forget to call the close() method of the vtkPipeline mixin
        introspectModuleMixin.close(self)
        # take out our view interface
        if self._view_frame is not None:
            self._view_frame.Destroy()
            
        # get rid of our reference
        del self._imageGaussianSmooth
        # and finally call our base dtor
        moduleBase.close(self)
        
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
        # continue with textToTuple in genUtils
        stdText = self._view_frame.stdTextCtrl.GetValue()
        self._config.standardDeviation = genUtils.textToTypeTuple(
            stdText, self._config.standardDeviation, 3, float)
        
        cutoffText = self._view_frame.radiusCutoffTextCtrl.GetValue()
        self._config.radiusCutoff = genUtils.textToTypeTuple(
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
            self._moduleManager.sync_module_view_with_logic(self)
            
        # if the window was visible already. just raise it
        self._view_frame.Show(True)
        self._view_frame.Raise()

    def _createViewFrame(self):
        self._moduleManager.importReload(
            'modules.filters.resources.python.imageGaussianSmoothViewFrame')
        import modules.filters.resources.python.imageGaussianSmoothViewFrame

        self._view_frame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager,
            modules.filters.resources.python.imageGaussianSmoothViewFrame.\
            imageGaussianSmoothViewFrame)

        objectDict = {'vtkImageGaussianSmooth' : self._imageGaussianSmooth}
        moduleUtils.createStandardObjectAndPipelineIntrospection(
            self, self._view_frame, self._view_frame.viewFramePanel,
            objectDict, None)

        moduleUtils.createECASButtons(self, self._view_frame,
                                      self._view_frame.viewFramePanel)

