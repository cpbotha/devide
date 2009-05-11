# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

import comedi_utils
reload(comedi_utils)
import vtk
import vtktudoss
from module_kits import vtk_kit
import wx


###########################################################################
# 2D:
# * vtkRectilinearWipeWidget, de-emphasize anything outside focus:
#   yellow blue inside, grey outside
# * IPW with yellow-blue difference inside focus, grey data1 outside
# * gradient of data2 overlaid on data1
# * two colour channels, for scalar and for gradient combination (you
#   should be able to do this wiht pre-proc, colourise data BEFORE)
# 3D:
# * context gray (silhouette, data1), focus animated
# * context gray (silhouette, data2), focus difference image

###########################################################################
class ComparisonMode:
    def __init__(self, comedi, cfg_dict):
        pass

    def set_inputs(self, data1, data2, data2m, distance):
        pass

    def update_vis(self):
        """If all inputs are available, update the visualisation.

        This also has to be called if there is no valid registered
        output anymore so that the view can be disabled.
        """
        pass

###########################################################################
class CheckerboardCM(ComparisonMode):
    """Comparison mode that shows a checkerboard of the two matched
    datasets.
    """

    def __init__(self, comedi, cfg_dict):
        self._comedi = comedi
        self._cfg = cfg_dict
        
        rwi,ren = comedi.get_compvis_vtk()
        self._sv = comedi_utils.CMSliceViewer(rwi, ren)
        comedi.sync_slice_viewers.add_slice_viewer(self._sv)

        self._cb = vtk.vtkImageCheckerboard()

        # we'll store our local bindings here
        self._d1 = None
        self._d2m = None

    def close(self):
        self._comedi.sync_slice_viewers.remove_slice_viewer(self._sv)
        self._sv.close()
        # disconnect the checkerboard
        self._cb.SetInput1(None)
        self._cb.SetInput2(None)

    def update_vis(self):
        # if there's valid data, do the vis man!
        d2m = self._comedi.get_data2m()
        d1 = self._comedi.get_data1()

        new_data = False

        if d1 != self._d1:
            self._d1 = d1
            self._cb.SetInput1(d1)
            new_data = True

        if d2m != self._d2m:
            self._d2m = d2m
            self._cb.SetInput2(d2m)
            new_data = True

        if new_data:
            # this means the situation has changed
            if d1 and d2m:
                # we have two datasets and can checkerboard them
                # enable the slice viewer
                self._sv.set_input(self._cb.GetOutput())
                # sync it to data1
                sv1 = self._comedi._data1_slice_viewer
                self._comedi.sync_slice_viewers.sync_all(
                        sv1, [self._sv])

            else:
                # this means one of our datasets is NULL
                # disable the slice viewer
                self._sv.set_input(None)

        # now check for UI things
        cp = self._comedi._view_frame.pane_controls.window
        divx = cp.cm_checkerboard_divx.GetValue()
        divy = cp.cm_checkerboard_divy.GetValue()
        divz = cp.cm_checkerboard_divz.GetValue()

        ndiv = self._cb.GetNumberOfDivisions()
        if ndiv != (divx, divy, divz):
            self._cb.SetNumberOfDivisions((divx, divy, divz))



        # we do render to update the 3D view
        self._sv.render()

###########################################################################
class Data2MCM(ComparisonMode):
    """Match mode that only displays the matched data2.
    """

    def __init__(self, comedi, cfg_dict):
        self._comedi = comedi
        self._cfg = cfg_dict

        rwi,ren = comedi.get_compvis_vtk()
        self._sv = comedi_utils.CMSliceViewer(rwi, ren)
        comedi.sync_slice_viewers.add_slice_viewer(self._sv)

    def close(self):
        self._comedi.sync_slice_viewers.remove_slice_viewer(self._sv)
        self._sv.close()

    def update_vis(self):
        # if there's valid data, do the vis man!
        o = self._comedi.match_mode.get_output()

        # get current input
        ci = self._sv.get_input()

        if o != ci:
            # new data!  do something!
            self._sv.set_input(o)

            # if it's not null, sync with primary viewer
            if o is not None:
                sv1 = self._comedi._data1_slice_viewer
                self._comedi.sync_slice_viewers.sync_all(
                        sv1, [self._sv])


        # we do render to update the 3D view
        self._sv.render()

CMAP_BLUE_TO_YELLOW_KREKEL = 0
CMAP_HEAT_PL = 1
CMAP_BLUE_TO_YELLOW_PL = 2
CMAP_BLACK_TO_WHITE_PL = 3

class FocusDiffCM(ComparisonMode):
    """Match mode that displays difference between data in focus area
    with blue/yellow colour scale, normal greyscale for the context.
    """

    # API methods ###################################################
    def __init__(self, comedi, cfg_dict):
        self._comedi = comedi
        self._cfg = cfg_dict

        # we'll store our local bindings here
        self._d1 = None
        self._d2m = None
        self._conf = None
        self._cmap_range = [-1024, 3072]
        self._cmap_type = CMAP_BLUE_TO_YELLOW_PL

        # color scales thingy
        self._color_scales = vtk_kit.color_scales.ColorScales()

        # instantiate us a slice viewer
        rwi,ren = comedi.get_compvis_vtk()
        self._sv = comedi_utils.CMSliceViewer(rwi, ren)
        # now make our own MapToColors
        ct = 32
        lut = self._sv.ipws[0].GetLookupTable()
        self._cmaps = [vtktudoss.vtkCVImageMapToColors() for _ in range(3)]
        for i,cmap in enumerate(self._cmaps):
            cmap.SetLookupTable(lut)
            cmap.SetConfidenceThreshold(ct)
            self._sv.ipws[i].SetColorMap(cmap)

        self._set_confidence_threshold_ui(ct)


        comedi.sync_slice_viewers.add_slice_viewer(self._sv)

        # now build up the VTK pipeline #############################
        # we'll use these to scale data between 0 and max.
        self._ss1 = vtk.vtkImageShiftScale()
        self._ss1.SetOutputScalarTypeToShort()
        self._ss2 = vtk.vtkImageShiftScale()
        self._ss2.SetOutputScalarTypeToShort()

        # we have to cast the confidence to shorts as well
        self._ssc = vtk.vtkImageShiftScale()
        self._ssc.SetOutputScalarTypeToShort()

        self._iac = vtk.vtkImageAppendComponents()
        # data1 will form the context
        self._iac.SetInput(0, self._ss1.GetOutput())
        # subtraction will form the focus
        self._iac.SetInput(1, self._ss2.GetOutput())
        # third input will be the confidence
        self._iac.SetInput(2, self._ssc.GetOutput())

        # event bindings ############################################
        self._bind_events()



    def close(self):
        self._unbind_events()
        self._comedi.sync_slice_viewers.remove_slice_viewer(self._sv)
        self._sv.close()

        # take care of all our bindings to VTK classes
        del self._ss1
        del self._ss2

    def update_vis(self):
        # if there's valid data, do the vis man!
        d2m = self._comedi.get_data2m()
        d1 = self._comedi.get_data1()
        conf = self._comedi.match_mode.get_confidence()

        new_data = False

        if d1 != self._d1:
            self._d1 = d1
            self._ss1.SetInput(d1)
            new_data = True

        if d2m != self._d2m:
            self._d2m = d2m
            self._ss2.SetInput(d2m)
            new_data = True

        if conf != self._conf:
            self._conf = conf
            self._ssc.SetInput(self._conf)

        if d1 and d2m and conf:
            if new_data:
                self._ss1.Update()
                self._ss2.Update()
                r = self._ss1.GetOutput().GetScalarRange()
                self._set_cmap_type_and_range(
                        CMAP_BLUE_TO_YELLOW_PL, r, True)
                self._set_range_ui(r)

                print "about to update iac"
                self._iac.SetNumberOfThreads(1)
                self._iac.Update()
                print "done updating iac"

                self._sv.set_input(self._iac.GetOutput())

                # sync it to data1
                sv1 = self._comedi._data1_slice_viewer
                self._comedi.sync_slice_viewers.sync_all(
                        sv1, [self._sv])
            else:
                # now new data, but we might want to update the
                # vis-settings
                self._handler_conf_thresh(event)
                self._sync_cmap_type_and_range_with_ui()

        else:
            self._sv.set_input(None)


        # we do render to update the 3D view
        self._sv.render()


    # PRIVATE methods ###############################################
    def _bind_events(self):
        vf = self._comedi._view_frame
        panel = vf.pane_controls.window

        panel.cm_diff_conf_thresh_txt.Bind(
                wx.EVT_TEXT_ENTER,
                self._handler_conf_thresh)

        panel.cm_diff_context_target_choice.Bind(
                wx.EVT_CHOICE,
                self._handler_focus_context_choice)

        panel.cm_diff_focus_target_choice.Bind(
                wx.EVT_CHOICE,
                self._handler_focus_target_choice)

        panel.cm_diff_cmap_choice.Bind(
                wx.EVT_CHOICE,
                self._handler_cmap_choice)

        panel.cm_diff_range0_text.Bind(
                wx.EVT_TEXT_ENTER,
                self._handler_range0)

        panel.cm_diff_range1_text.Bind(
                wx.EVT_TEXT_ENTER,
                self._handler_range1)

    def _handler_cmap_choice(self, event):
        self._sync_cmap_type_and_range_with_ui()

    def _handler_conf_thresh(self, event):
        vf = self._comedi._view_frame
        panel = vf.pane_controls.window

        v = panel.cm_diff_conf_thresh_txt.GetValue()

        try:
            v = float(v)
        except ValueError:
            v = self._cmaps[0].GetConfidenceThreshold()
            self._set_confidence_threshold_ui(v)
        else:
            [cmap.SetConfidenceThreshold(v) for cmap in self._cmaps]

        self._sv.render()

    def _handler_focus_context_choice(self, event):
        c = event.GetEventObject()
        val = c.GetSelection()
        if val != self._cmaps[0].GetContextTarget():
            [cmap.SetContextTarget(val) for cmap in self._cmaps]

            self._sv.render()

    def _handler_range0(self, event):
        self._sync_cmap_type_and_range_with_ui()

    def _handler_range1(self, event):
        self._sync_cmap_type_and_range_with_ui()

    def _handler_focus_target_choice(self, event):
        c = event.GetEventObject()
        val = c.GetSelection()
        if val != self._cmaps[0].GetFocusTarget():
            [cmap.SetFocusTarget(val) for cmap in self._cmaps]

            self._sv.render()

    def _set_confidence_threshold_ui(self, thresh):
        vf = self._comedi._view_frame
        panel = vf.pane_controls.window

        panel.cm_diff_conf_thresh_txt.SetValue('%.1f' % (thresh,))

    def _set_range_ui(self, range):
        """Set the given range in the interface.
        """
        vf = self._comedi._view_frame
        panel = vf.pane_controls.window

        r = range
        panel.cm_diff_range0_text.SetValue(str(r[0]))
        panel.cm_diff_range1_text.SetValue(str(r[1]))


    def _unbind_events(self):
        vf = self._comedi._view_frame
        panel = vf.pane_controls.window


        panel.cm_diff_context_target_choice.Unbind(
                wx.EVT_CHOICE)
        panel.cm_diff_focus_target_choice.Unbind(
                wx.EVT_CHOICE)

        panel.cm_diff_range0_text.Unbind(
                wx.EVT_TEXT_ENTER)

        panel.cm_diff_range1_text.Unbind(
                wx.EVT_TEXT_ENTER)

    def _set_cmap_type_and_range(self, cmap_type, range,
            force_update=False):
        """First sanitise, then synchronise the current colormap range
        to the specified UI values, also taking into account the
        current colour map choice.
        """

        vf = self._comedi._view_frame
        panel = vf.pane_controls.window

        r0 = panel.cm_diff_range0_text.GetValue()
        r1 = panel.cm_diff_range1_text.GetValue()

        try:
            r0 = float(r0)
        except ValueError:
            r0 = self._cmap_range[0]

        try:
            r1 = float(r1)
        except ValueError:
            r1 = self._cmap_range[1]

        # swap if necessary
        if r0 > r1:
            r1,r0 = r0,r1

        r = r0,r1

        if force_update:
            must_update = True
        else:
            must_update = False

        if r0 != self._cmap_range[0] or r1 != self._cmap_range[1]:
            must_update = True
            self._cmap_range = r

        if cmap_type != self._cmap_type:
            must_update = True
            self._cmap_type = cmap_type

        if must_update:
            if cmap_type == CMAP_BLUE_TO_YELLOW_KREKEL:
                lut = self._color_scales.LUT_BlueToYellow(r)
            elif cmap_type == CMAP_HEAT_PL:
                lut = self._color_scales.LUT_Linear_Heat(r)
            elif cmap_type == CMAP_BLUE_TO_YELLOW_PL:
                lut = self._color_scales.LUT_Linear_BlueToYellow(r)
            elif cmap_type == CMAP_BLACK_TO_WHITE_PL:
                lut = self._color_scales.LUT_Linear_BlackToWhite(r)

            for cmap in self._cmaps:
                cmap.SetLookupTable2(lut)

            self._sv.render()

        # we return the possibly corrected range
        return r

    def _sync_cmap_type_and_range_with_ui(self):

        vf = self._comedi._view_frame
        panel = vf.pane_controls.window

        r0 = panel.cm_diff_range0_text.GetValue()
        r1 = panel.cm_diff_range0_text.GetValue()
        cmap_type = panel.cm_diff_cmap_choice.GetSelection()

        r = self._set_cmap_type_and_range(cmap_type, (r0,r1))

        if r[0] != r0 or r[1] != r1:
            self._set_range_ui(r)

        



    # PUBLIC methods ################################################

