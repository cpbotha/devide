# dtsc_seg_flt.py copyright (c) 2002 Charl P. Botha <cpbotha@ieee.org>
# $Id: dtsc_seg_flt.py,v 1.2 2002/09/10 15:54:58 cpbotha Exp $
# double-threshold seed connectivity segmentation filter

from gen_utils import log_error
from module_base import module_base, module_mixin_vtk_pipeline_config
import vtk
import vtkcpbothapython
from wxPython.wx import *
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor

class dtsc_seg_flt(module_base,
                   module_mixin_vtk_pipeline_config):

    """Double threshold seed connectivity segmentor.

    This will perform a upper/lower threshold on the input data, thus
    binarising it and then perform a seed-initialised connectivity
    analysis.
    """

    def __init__(self, module_manager):
        # call parent __init__
        module_base.__init__(self, module_manager)

        # setup VTK pipeline
        self._threshold = vtk.vtkImageThreshold()
        self._seedconnect = vtk.vtkImageSeedConnectivity()
        self._seedconnect.SetInput(self._threshold.GetOutput())

        # create gui
        pw = self._module_manager.get_module_view_parent_view_parent_window()
        self._view_frame = self._create_view_frame(pw)

    #################################################################
    # module API methods
    #################################################################

    def close(self):
        pass

    def get_input_descriptions(self):
        return ('Seed points (vtkPoints)',
                'Volume data (vtkImageData)')

    def set_input(self, idx, input_stream):
        pass

    def get_output_descriptions(self):
        return ('Segmented data (vtkImageData)',)

    def get_output(self):
        pass

    def view(self):
        pass

    #################################################################
    # utility methods
    #################################################################

    def _create_view_frame(self, parent_window):

        pass

