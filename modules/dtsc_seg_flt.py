# dtsc_seg_flt.py copyright (c) 2002 Charl P. Botha <cpbotha@ieee.org>
# $Id: dtsc_seg_flt.py,v 1.1 2002/09/09 15:40:34 cpbotha Exp $
# double-threshold seed connectivity segmentation filter

from gen_utils import log_error
from module_base import module_base, module_mixin_vtk_pipeline_config
import vtk
import vtkcpbothapython
from wxPython.wx import *
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor

class dtsc_seg_flt(module_base,
                       module_mixin_vtk_pipeline_config):

    def __init__(self, module_manager):
        
        module_base.__init__(self, module_manager)

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

