# imageGaussianSmooth copyright (c) 2003 by Charl P. Botha cpbotha@ieee.org
# $Id$
# performs image smoothing by convolving with a Gaussian

import gen_utils
from module_base import ModuleBase
from module_mixins import IntrospectModuleMixin
import module_utils
import vtk

class resampleImage(IntrospectModuleMixin, ModuleBase):

    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        self._imageResample = vtk.vtkImageResample()

        module_utils.setup_vtk_object_progress(self, self._imageResample,
                                           'Resampling image.')
        
        # 0: nearest neighbour
        # 1: linear
        # 2: cubic
        self._config.interpolationMode = 1
        self._config.magFactors = [1.0, 1.0, 1.0]

        self._view_frame = None

        self.sync_module_logic_with_config()
        
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
        del self._imageResample
        # and finally call our base dtor
        ModuleBase.close(self)
        
    def get_input_descriptions(self):
        return ('vtkImageData',)

    def set_input(self, idx, inputStream):
        self._imageResample.SetInput(inputStream)

    def get_output_descriptions(self):
        return (self._imageResample.GetOutput().GetClassName(),)

    def get_output(self, idx):
        return self._imageResample.GetOutput()

    def logic_to_config(self):
        istr = self._imageResample.GetInterpolationModeAsString()
        # we do it this way so that when the values in vtkImageReslice
        # are changed, we won't be affected
        self._config.interpolationMode = {'NearestNeighbor': 0,
                                          'Linear': 1,
                                          'Cubic': 2}[istr]

        
        for i in range(3):
            mfi = self._imageResample.GetAxisMagnificationFactor(i, None)
            self._config.magFactors[i] = mfi

    def config_to_logic(self):
        if self._config.interpolationMode == 0:
            self._imageResample.SetInterpolationModeToNearestNeighbor()
        elif self._config.interpolationMode == 1:
            self._imageResample.SetInterpolationModeToLinear()
        else:
            self._imageResample.SetInterpolationModeToCubic()

        for i in range(3):
            self._imageResample.SetAxisMagnificationFactor(
                i, self._config.magFactors[i])

    def view_to_config(self):
        itc = self._view_frame.interpolationTypeChoice.GetSelection()
        if itc < 0 or itc > 2:
            # default when something weird happens to choice
            itc = 1

        self._config.interpolationMode = itc

        txtTup = self._view_frame.magFactorXText.GetValue(), \
                 self._view_frame.magFactorYText.GetValue(), \
                 self._view_frame.magFactorZText.GetValue()

        for i in range(3):
            self._config.magFactors[i] = gen_utils.textToFloat(
                txtTup[i], self._config.magFactors[i])
            
        
    def config_to_view(self):
        self._view_frame.interpolationTypeChoice.SetSelection(
            self._config.interpolationMode)

        txtTup = self._view_frame.magFactorXText, \
                 self._view_frame.magFactorYText, \
                 self._view_frame.magFactorZText
        
        for i in range(3):
            txtTup[i].SetValue(str(self._config.magFactors[i]))
        
    
    def execute_module(self):
        self._imageResample.Update()

    def streaming_execute_module(self):
        self._imageResample.GetOutput().Update()

    def view(self, parent_window=None):
        if self._view_frame is None:
            self._createViewFrame()
            
        # if the window was visible already. just raise it
        self._view_frame.Show(True)
        self._view_frame.Raise()

    def _createViewFrame(self):
        self._module_manager.import_reload(
            'modules.filters.resources.python.resampleImageViewFrame')
        import modules.filters.resources.python.resampleImageViewFrame

        self._view_frame = module_utils.instantiate_module_view_frame(
            self, self._module_manager,
            modules.filters.resources.python.resampleImageViewFrame.\
            resampleImageViewFrame)

        objectDict = {'vtkImageResample' : self._imageResample}
        module_utils.create_standard_object_introspection(
            self, self._view_frame, self._view_frame.viewFramePanel,
            objectDict, None)

        module_utils.create_eoca_buttons(self, self._view_frame,
                                      self._view_frame.viewFramePanel)
