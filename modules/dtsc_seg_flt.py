# dtsc_seg_flt.py copyright (c) 2002 Charl P. Botha <cpbotha@ieee.org>
# $Id: dtsc_seg_flt.py,v 1.3 2002/09/10 16:14:27 cpbotha Exp $
# double-threshold seed connectivity segmentation filter

from gen_utils import log_error
from module_base import module_base, module_mixin_vtk_pipeline_config
import module_utils
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
        self._create_view_frame()

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
        self._view_frame.Show(true)

    #################################################################
    # utility methods
    #################################################################

    def _create_view_frame(self):
        pw = self._module_manager.get_module_view_parent_window()
        self._view_frame = dtsc_seg_flt_view_frame(parent=pw, id=-1, title='')
        EVT_CLOSE(self._view_frame,
                  lambda e, s=self: s._view_frame.Show(false))
        module_utils.bind_CSAEO2(self, self._view_frame)        


class dtsc_seg_flt_view_frame(wxFrame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: __init__
        kwds["style"] = wxCAPTION|wxMINIMIZE_BOX|wxMAXIMIZE_BOX|wxSYSTEM_MENU|wxRESIZE_BORDER
        wxFrame.__init__(self, *args, **kwds)
        self.label_8 = wxStaticText(self, -1, "Lower threshold:")
        self.lt_spinctrl = wxSpinCtrl(self, -1, min=0, max=100, initial=0, style=wxSP_ARROW_KEYS)
        self.label_12 = wxStaticText(self, -1, "Upper threshold:")
        self.ut_spinctrl = wxSpinCtrl(self, -1, min=0, max=100, initial=0, style=wxSP_ARROW_KEYS)
        self.label_1 = wxStaticText(self, -1, "Examine the")
        self.VTK_OBJECT_CHOICE_ID  =  wxNewId()
        self.object_choice = wxChoice(self, self.VTK_OBJECT_CHOICE_ID , choices=['vtkImageThreshold', 'vtkImageSeedConnectivity'])
        self.label_2 = wxStaticText(self, -1, "or")
        self.VTK_PIPELINE_ID  =  wxNewId()
        self.pipeline_button = wxButton(self, self.VTK_PIPELINE_ID , "Pipeline")
        self.cancel_button = wxButton(self, wxID_CANCEL, "Cancel")
        self.SYNC_ID  =  wxNewId()
        self.sync_button = wxButton(self, self.SYNC_ID , "Sync")
        self.APPLY_ID  =  wxNewId()
        self.apply_button = wxButton(self, self.APPLY_ID , "Apply")
        self.EXECUTE_ID  =  wxNewId()
        self.execute_button = wxButton(self, self.EXECUTE_ID , "Execute")
        self.ok_button = wxButton(self, wxID_OK, "OK")

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: __set_properties
        self.SetTitle("dtsc segmentor view")
        self.object_choice.SetSelection(0)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: __do_layout
        sizer_1 = wxBoxSizer(wxVERTICAL)
        sizer_2 = wxBoxSizer(wxHORIZONTAL)
        sizer_4 = wxBoxSizer(wxHORIZONTAL)
        sizer_3 = wxBoxSizer(wxHORIZONTAL)
        sizer_3.Add(self.label_8, 0, wxLEFT|wxRIGHT|wxALIGN_CENTER_VERTICAL, 2)
        sizer_3.Add(self.lt_spinctrl, 0, 0, 0)
        sizer_3.Add(self.label_12, 0, wxLEFT|wxRIGHT|wxALIGN_CENTER_VERTICAL, 5)
        sizer_3.Add(self.ut_spinctrl, 0, 0, 0)
        sizer_1.Add(sizer_3, 1, wxALL|wxEXPAND, 5)
        sizer_4.Add(self.label_1, 0, wxLEFT|wxRIGHT|wxALIGN_CENTER_VERTICAL, 2)
        sizer_4.Add(self.object_choice, 0, wxALIGN_CENTER_VERTICAL, 0)
        sizer_4.Add(self.label_2, 0, wxLEFT|wxRIGHT|wxALIGN_CENTER_VERTICAL, 2)
        sizer_4.Add(self.pipeline_button, 0, wxALIGN_CENTER_VERTICAL, 0)
        sizer_1.Add(sizer_4, 1, wxALL|wxEXPAND, 5)
        sizer_2.Add(self.cancel_button, 0, wxALL, 2)
        sizer_2.Add(self.sync_button, 0, wxALL, 2)
        sizer_2.Add(self.apply_button, 0, wxALL, 2)
        sizer_2.Add(self.execute_button, 0, wxALL, 2)
        sizer_2.Add(self.ok_button, 0, wxALL, 2)
        sizer_1.Add(sizer_2, 0, wxALL, 5)
        self.SetAutoLayout(1)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()
        # end wxGlade

# end of class dtsc_seg_flt_view_frame


