# dtsc_seg_flt.py copyright (c) 2002 Charl P. Botha <cpbotha@ieee.org>
# $Id: dtsc_seg_flt.py,v 1.6 2003/01/08 16:16:57 cpbotha Exp $
# double-threshold seed connectivity segmentation filter

from gen_utils import log_error
from module_base import module_base, module_mixin_vtk_pipeline_config
import module_utils
import vtk
from wxPython.wx import *
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor

class dtsc_seg_flt(module_base,
                   module_mixin_vtk_pipeline_config):

    """Double threshold seed connectivity segmentor.

    This will perform a upper/lower threshold on the input data, thus
    binarising it and then perform a seed-initialised connectivity
    analysis.

    Inputs: Seed points, e.g. vtkPoints output of vtk_slice_vwr.py
            Volume data, e.g. vtkImageData from vtk_dicom_rdr.py

    Output: Segmented volume data.
    """

    def __init__(self, module_manager):
        # call parent __init__
        module_base.__init__(self, module_manager)

        # setup VTK pipeline
        mm = self._module_manager
        self._input_points = None
        self._points_obs_id = -1        
        
        self._threshold = vtk.vtkImageThreshold()
        self._threshold.SetInValue(1)
        self._threshold.SetOutValue(0)
        self._threshold.SetOutputScalarTypeToUnsignedChar()
        self._threshold.SetProgressText('Thresholding data')
        self._threshold.SetProgressMethod(lambda s=self, mm=mm:
                                          mm.vtk_progress_cb(s._threshold))

        
        self._seedconnect = vtk.vtkImageSeedConnectivity()
        self._seedconnect.SetInput(self._threshold.GetOutput())
        self._seedconnect.SetInputConnectValue(1)
        self._seedconnect.SetProgressText('Performing region growing')
        self._seedconnect.SetProgressMethod(lambda s=self, mm=mm:
                                            mm.vtk_progress_cb(s._seedconnect))

        # create gui
        self._create_view_frame()

        self.sync_config()

    #################################################################
    # module API methods
    #################################################################

    def apply_config(self):
        lt = self._view_frame.lt_spinctrl.GetValue()
        ut = self._view_frame.ut_spinctrl.GetValue()
        self._threshold.ThresholdBetween(lt, ut)

    def close(self):
        self._view_frame.Destroy()
        del self._threshold
        del self._seedconnect
        del self._input_points

    def execute_module(self):
        self._seedconnect.Update()
        self._module_manager.vtk_poll_error()

    def get_input_descriptions(self):
        return ('Seed points (vtkPoints)',
                'Volume data (vtkImageData)')
    
    def get_output(self, idx):
        if idx == 0:
            return self._seedconnect.GetOutput()
        else:
            wxLogError('Invalid output requested from dtsc_seg_flt.')

    def get_output_descriptions(self):
        return ('Segmented data (vtkImageData)',)

    def set_input(self, idx, input_stream):
        if input_stream == None:
            if idx == 0:
                if self._input_points and self._points_obs_id >= 0:
                    # we have to remove our observer
                    self._input_points.RemoveObserver(self._points_obs_id)
                    self._points_obs_id = -1
                    # because we do this, the vtkImageSeedConnectivity will
                    # retain the last added values
                    
                self._input_points = None
                
            else:
                self._threshold.SetInput(None)
                
        else:
            if hasattr(input_stream, 'IsA') and \
               callable(input_stream.IsA):
                if input_stream.IsA('vtkPoints'):
                    if idx == 0:
                        self._input_points = input_stream
                        # and add an observer
                        self._points_obs_id = self._input_points.AddObserver(
                            'ModifiedEvent',
                            self._points_mod_cb)
                        # also make sure that the initial state is fed through
                        self._points_mod_cb(None, None)
                        
                    else:
                        raise TypeError, 'vtkPoints should be connected on ' \
                              'the first input.'
                    
                elif input_stream.IsA('vtkImageData'):
                    if idx == 0:
                        raise TypeError, 'vtkImageData should be connected ' \
                              ' the second input.'
                    else:
                        self._threshold.SetInput(input_stream)
                        # and sync us up
                        self.sync_config()
                else:
                    raise TypeError, 'vtkPoints or vtkImageData input '\
                          'required.'
            else:
                raise TypeError, 'vtkPoints or vtkImageData input '\
                      'required.'             

    def sync_config(self):
        if self._threshold.GetInput():
            self._threshold.GetInput().Update()
            minv,maxv = self._threshold.GetInput().GetScalarRange()
        else:
            minv = 0.0
            maxv = 100.0

        # do we want to do this dynamically? i.e. the lt's max is the
        # ut's min?
        self._view_frame.lt_spinctrl.SetRange(minv, maxv)
        self._view_frame.ut_spinctrl.SetRange(minv, maxv)        
            
        ut = self._threshold.GetUpperThreshold()
        if ut < minv:
            ut = minv
        if ut > maxv:
            ut = maxv
            
        lt = self._threshold.GetLowerThreshold()
        if lt < minv:
            lt = minv
        if lt > maxv:
            lt = maxv

        self._view_frame.lt_spinctrl.SetValue(lt)
        self._view_frame.ut_spinctrl.SetValue(ut)

    def view(self):
        self.sync_config()
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

    #################################################################
    # utility methods
    #################################################################

    def _points_mod_cb(self, evt, obj):
        """Callback to keep an eye on our input_points.

        Whenever input_points is changed (i.e. its Modified() is called)
        this callback will be invoked.  This handler will make sure that
        all the coords in input_points are transferred as seedpoints
        to the vtkImageSeedConnectivity filter.

        If the user disconnects us from an input points, this handler is
        disconnected from that object.  This means the seed points in the
        vtkImageSeedConnectivity will remain constant until we get
        reconnected with a valid vtkPoints again!
        """
        
        if self._input_points:
            self._seedconnect.RemoveAllSeeds()
            for i in range(self._input_points.GetNumberOfPoints()):
                x,y,z = self._input_points.GetPoint(i)
                self._seedconnect.AddSeed(x,y,z)
        



## wxGlade stuff ####################################################
        
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


