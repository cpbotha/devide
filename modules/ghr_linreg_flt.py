# ghr_linreg_flt.py copyright (c) 2002 Charl P. Botha <cpbotha@ieee.org>
# $Id: ghr_linreg_flt.py,v 1.4 2003/03/09 23:34:26 cpbotha Exp $
# double-threshold seed connectivity segmentation filter

from gen_utils import log_error
from module_base import module_base, module_mixin_vtk_pipeline_config
import module_utils
import vtk
from wxPython.wx import *
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor

class ghr_linreg_flt(module_base,
                     module_mixin_vtk_pipeline_config):
    """GH-r linear regression filter.

    Determines gleno-humeral centre of rotation with a linear regression
    formula.

    Inputs: Seed points, e.g. vtkPoints output of vtk_slice_vwr.py
            Seed point names, e.g. string list output of vtk_slice_vwr.py

    Output: vtkPoints with GH-r centre of rotation.
    """

    def __init__(self, module_manager):
        module_base.__init__(self, module_manager)
        # default Meskers
        self._regression = 'Meskers'
        self._create_view_frame()

        # our local copies of these
        self._vtk_points = None
        self._vtk_points_names = None

    #################################################################
    # module API methods
    #################################################################

    def apply_config(self):
        self._view_frame.regression_combobox.SetValue(self._regression)

    def close(self):
        self._view_frame.Destroy()
        del self._vtk_points
        del self._vtk_points_names

    def execute_module(self):
        if self._vtk_points is None:
            wxLogError("ghr_linreg_flt has no vtkPoints input!")
            return
        
        if self._vtk_points_names is None:
            wxLogError("ghr_linreg_flt has no landmark names input!")
            return

        print self._vtk_points_names

    def get_input_descriptions(self):
        return ('Scapular landmarks (vtkPoints)',
                'Landmark names (list)')

    def get_output(self, idx):
        raise Exception

    def get_output_descriptions(self):
        return ()

    def set_input(self, idx, input_stream):
        if idx == 0:
            if input_stream is None:
                # disconnect
                self._vtk_points = None
            elif hasattr(input_stream, 'GetClassName') and \
               input_stream.IsA('vtkPoints'):
                self._vtk_points = input_stream
            else:
                raise TypeError, \
                      "You have tried to connect a non-vtkPoints type to " \
                      "the ghr_linreg_flt vtkPoints input."
        else:
            if input_stream is None:
                self._vtk_points_names = None
            elif type(input_stream) == type([]):
                self._vtk_points_names = input_stream
            else:
                raise TypeError, \
                      "You have tried to connect a non-list type to " \
                      "the ghr_linreg_flt landmark names input."

    def sync_config(self):
        self._regression = self._view_frame.regression_combobox.GetValue()

    def view(self):
        self.sync_config()
        self._view_frame.Show(True)

    #################################################################
    # utility methods
    #################################################################

    def _create_view_frame(self):
        pw = self._module_manager.get_module_view_parent_window()
        self._view_frame = ghr_linreg_flt_view_frame(parent=pw, id=-1,
                                                     title='')
        EVT_CLOSE(self._view_frame,
                  lambda e, s=self: s._view_frame.Show(false))
        module_utils.bind_CSAEO2(self, self._view_frame)

## wxGlade stuff ####################################################
        
class ghr_linreg_flt_view_frame(wxFrame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: __init__
        kwds["style"] = wxCAPTION|wxMINIMIZE_BOX|wxMAXIMIZE_BOX|wxSYSTEM_MENU|wxRESIZE_BORDER
        wxFrame.__init__(self, *args, **kwds)
        self.label_4 = wxStaticText(self, -1, "Select regression")
        self.regression_combobox = wxComboBox(self, -1, choices=['Meskers'], style=wxCB_DROPDOWN|wxCB_READONLY)
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
        self.SetTitle("GH-r linear regression view")
        self.regression_combobox.SetSelection(0)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: __do_layout
        sizer_1 = wxBoxSizer(wxVERTICAL)
        sizer_2 = wxBoxSizer(wxHORIZONTAL)
        grid_sizer_1 = wxFlexGridSizer(1, 2, 0, 0)
        grid_sizer_1.Add(self.label_4, 0, wxLEFT|wxRIGHT|wxALIGN_CENTER_VERTICAL, 2)
        grid_sizer_1.Add(self.regression_combobox, 1, wxALL|wxEXPAND|wxALIGN_CENTER_VERTICAL, 0)
        sizer_1.Add(grid_sizer_1, 1, wxALL|wxEXPAND, 5)
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

# end of class ghr_linreg_flt_view_frame


