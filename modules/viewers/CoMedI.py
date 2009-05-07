# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

# skeleton of an AUI-based viewer module
# copy and modify for your own purposes.

# set to False for 3D viewer, True for 2D image viewer
IMAGE_VIEWER = True

MATCH_MODE_PASSTHROUGH = 0
MATCH_MODE_LANDMARK_SS = 1

MATCH_MODE_STRINGS = [ \
        'Single structure landmarks'
        ]

COMPARISON_MODE_DATA2M = 0
COMPARISON_MODE_CHECKERBOARD = 1

# import the frame, i.e. the wx window containing everything
import CoMedIFrame
# and do a reload, so that the GUI is also updated at reloads of this
# module.
reload(CoMedIFrame)

import comedi_match_modes
reload(comedi_match_modes)

from external.ObjectListView import ColumnDefn, EVT_CELL_EDIT_FINISHING
import math
from module_kits.misc_kit import misc_utils
from module_kits.vtk_kit.utils import DVOrientationWidget
from module_base import ModuleBase
from module_mixins import IntrospectModuleMixin
import module_utils
import operator
import os
import random #temp testing
import sys
import traceback
import vtk
import wx

###########################################################################
class SyncSliceViewers:
    """Class to link a number of CMSliceViewer instances w.r.t.
    camera.

    FIXME: consider adding option to block certain slice viewers from
    participation.  Is this better than just removing them?
    """

    def __init__(self):
        # store all slice viewer instances that are being synced
        self.slice_viewers = []
        self.observer_tags = {}
        # if set to False, no syncing is done.
        # user is responsible for doing the initial sync with sync_all
        # after this variable is toggled from False to True
        self.sync = True

    def add_slice_viewer(self, slice_viewer):
        if slice_viewer in self.slice_viewers:
            return

        # we'll use this to store all observer tags for this
        # slice_viewer
        t = self.observer_tags[slice_viewer] = {}


        istyle = slice_viewer.rwi.GetInteractorStyle()

        # the following two observers are workarounds for a bug in VTK
        # the interactorstyle does NOT invoke an InteractionEvent at
        # mousewheel, so we make sure it does in our workaround
        # observers.
        t['istyle MouseWheelForwardEvent'] = \
                istyle.AddObserver('MouseWheelForwardEvent',
                self._observer_mousewheel_forward)

        t['istyle MouseWheelBackwardEvent'] = \
                istyle.AddObserver('MouseWheelBackwardEvent',
                self._observer_mousewheel_backward)

        # this one only gets called for camera interaction (of course)
        t['istyle InteractionEvent'] = \
                istyle.AddObserver('InteractionEvent',
                lambda o,e: self._observer_camera(slice_viewer))

        # this gets call for all interaction with the slice
        # (cursoring, slice pushing, perhaps WL)
        for idx in range(3):
            # note the i=idx in the lambda expression.  This is
            # because that gets evaluated at define time, whilst the
            # body of the lambda expression gets evaluated at
            # call-time
            t['ipw%d InteractionEvent' % (idx,)] = \
                slice_viewer.ipws[idx].AddObserver('InteractionEvent',
                lambda o,e,i=idx: self._observer_ipw(slice_viewer, i))

            t['ipw%d WindowLevelEvent' % (idx,)] = \
                slice_viewer.ipws[idx].AddObserver('WindowLevelEvent',
                lambda o,e,i=idx: self._observer_window_level(slice_viewer,i))

        self.slice_viewers.append(slice_viewer)

    def close(self):
        for sv in self.slice_viewers:
            self.remove_slice_viewer(sv)

    def _observer_camera(self, sv):
        """This observer will keep the cameras of all the
        participating slice viewers synched.

        It's only called when the camera is moved.
        """
        if not self.sync:
            return

        cc = self.sync_cameras(sv)
        [sv.render() for sv in cc]

    def _observer_mousewheel_forward(self, vtk_o, vtk_e):
        vtk_o.OnMouseWheelForward()
        vtk_o.InvokeEvent('InteractionEvent')

    def _observer_mousewheel_backward(self, vtk_o, vtk_e):
        vtk_o.OnMouseWheelBackward()
        vtk_o.InvokeEvent('InteractionEvent')

    def _observer_ipw(self, slice_viewer, idx=0):
        """This is called whenever the user does ANYTHING with the
        IPW.
        """
        if not self.sync:
            return

        cc = self.sync_ipws(slice_viewer, idx)
        [sv.render() for sv in cc]

    def _observer_window_level(self, slice_viewer, idx=0):
        """This is called whenever the window/level is changed.  We
        don't have to render, because the SetWindowLevel() call does
        that already.
        """
        if not self.sync:
            return

        self.sync_window_level(slice_viewer, idx)

    def remove_slice_viewer(self, slice_viewer):
        if slice_viewer in self.slice_viewers:

            # first remove all observers that we might have added
            t = self.observer_tags[slice_viewer]
            istyle = slice_viewer.rwi.GetInteractorStyle()
            istyle.RemoveObserver(
                    t['istyle InteractionEvent'])
            istyle.RemoveObserver(
                    t['istyle MouseWheelForwardEvent'])
            istyle.RemoveObserver(
                    t['istyle MouseWheelBackwardEvent'])

            for idx in range(3):
                ipw = slice_viewer.ipws[idx]
                ipw.RemoveObserver(
                    t['ipw%d InteractionEvent' % (idx,)])
                ipw.RemoveObserver(
                    t['ipw%d WindowLevelEvent' % (idx,)])

            # then delete our record of these observer tags
            del self.observer_tags[slice_viewer]

            # then delete our record of the slice_viewer altogether
            idx = self.slice_viewers.index(slice_viewer)
            del self.slice_viewers[idx]

    def sync_cameras(self, sv, dest_svs=None):
        """Sync all cameras to that of sv.

        Returns a list of changed SVs (so that you know which ones to
        render).
        """
        cam = sv.renderer.GetActiveCamera()
        pos = cam.GetPosition()
        fp = cam.GetFocalPoint()
        vu = cam.GetViewUp()
        ps = cam.GetParallelScale()

        if dest_svs is None:
            dest_svs = self.slice_viewers

        changed_svs = []
        for other_sv in dest_svs:
            if not other_sv is sv:
                other_ren = other_sv.renderer
                other_cam = other_ren.GetActiveCamera()
                other_cam.SetPosition(pos)
                other_cam.SetFocalPoint(fp)
                other_cam.SetViewUp(vu)
                # you need this too, else the parallel mode does not
                # synchronise.
                other_cam.SetParallelScale(ps)
                other_ren.UpdateLightsGeometryToFollowCamera()
                other_ren.ResetCameraClippingRange()
                changed_svs.append(other_sv)

        return changed_svs

    def sync_ipws(self, sv, idx=0, dest_svs=None):
        """Sync all slice positions to that of sv.

        Returns a list of cahnged SVs so that you know on which to
        call render.
        """

        ipw = sv.ipws[idx]
        o,p1,p2 = ipw.GetOrigin(), \
                ipw.GetPoint1(), ipw.GetPoint2()

        if dest_svs is None:
            dest_svs = self.slice_viewers

        changed_svs = []
        for other_sv in dest_svs:
            if other_sv is not sv:
                other_ipw = other_sv.ipws[idx]
                # we only synchronise slice position if it's actually
                # changed.
                if o != other_ipw.GetOrigin() or \
                        p1 != other_ipw.GetPoint1() or \
                        p2 != other_ipw.GetPoint2():
                    other_ipw.SetOrigin(o)
                    other_ipw.SetPoint1(p1)
                    other_ipw.SetPoint2(p2)
                    other_ipw.UpdatePlacement()
                    changed_svs.append(other_sv)

        return changed_svs

    def sync_window_level(self, sv, idx=0, dest_svs=None):
        """Sync all window level settings with that of SV.

        Returns list of changed SVs: due to the SetWindowLevel call,
        these have already been rendered!
        """

        ipw = sv.ipws[idx]
        w,l = ipw.GetWindow(), ipw.GetLevel()

        if dest_svs is None:
            dest_svs = self.slice_viewers

        changed_svs = []
        for other_sv in dest_svs:
            if other_sv is not sv:
                other_ipw = other_sv.ipws[idx]

                if w != other_ipw.GetWindow() or \
                        l != other_ipw.GetLevel():
                            other_ipw.SetWindowLevel(w,l,0)
                            changed_svs.append(other_sv)


        return changed_svs

    def sync_all(self, sv, dest_svs=None):
        """Convenience function that performs all syncing possible of
        dest_svs to sv.  It also take care of making only the
        necessary render calls.
        """

        # FIXME: take into account all other slices too.
        c1 = set(self.sync_cameras(sv, dest_svs))
        c2 = set(self.sync_ipws(sv, 0, dest_svs))
        c3 = set(self.sync_window_level(sv, 0, dest_svs))

        # we only need to call render on SVs that are in c1 or c2, but
        # NOT in c3, because WindowLevel syncing already does a
        # render.  Use set operations for this: 
        c4 = (c1 | c2) - c3
        [isv.render() for isv in c4]

###########################################################################
class CMSliceViewer:
    """Simple class for enabling 1 or 3 ortho slices in a 3D scene.
    """

    def __init__(self, rwi, renderer):
        self.rwi = rwi
        self.renderer = renderer

        istyle = vtk.vtkInteractorStyleTrackballCamera()
        rwi.SetInteractorStyle(istyle)

        # we unbind the existing mousewheel handler so it doesn't
        # interfere
        rwi.Unbind(wx.EVT_MOUSEWHEEL)
        rwi.Bind(wx.EVT_MOUSEWHEEL, self._handler_mousewheel)

        self.ipws = [vtk.vtkImagePlaneWidget() for _ in range(3)]
        for ipw in self.ipws:
            ipw.SetInteractor(rwi)

        # we only set the picker on the visible IPW, else the
        # invisible IPWs block picking!
        self.picker = vtk.vtkCellPicker()
        self.picker.SetTolerance(0.005)
        self.ipws[0].SetPicker(self.picker)

        self.outline_source = vtk.vtkOutlineCornerFilter()
        m = vtk.vtkPolyDataMapper()
        m.SetInput(self.outline_source.GetOutput())
        a = vtk.vtkActor()
        a.SetMapper(m)
        a.PickableOff()
        self.outline_actor = a

        self.dv_orientation_widget = DVOrientationWidget(rwi)

        # this can be used by clients to store the current world
        # position
        self.current_world_pos = (0,0,0)
        self.current_index_pos = (0,0,0)

    def close(self):
        self.set_input(None)
        self.dv_orientation_widget.close()

    def activate_slice(self, idx):
        if idx in [1,2]:
            self.ipws[idx].SetEnabled(1)
            self.ipws[idx].SetPicker(self.picker)


    def deactivate_slice(self, idx):
        if idx in [1,2]:
            self.ipws[idx].SetEnabled(0)
            self.ipws[idx].SetPicker(None)

    def get_input(self):
        return self.ipws[0].GetInput()

    def get_world_pos(self, image_pos):
        """Given image coordinates, return the corresponding world
        position.
        """

        idata = self.get_input()
        if not idata:
            return None

        ispacing = idata.GetSpacing()
        iorigin = idata.GetOrigin()
        # calculate real coords
        world = map(operator.add, iorigin,
                    map(operator.mul, ispacing, image_pos[0:3]))

        return world



    def set_perspective(self):
        cam = self.renderer.GetActiveCamera()
        cam.ParallelProjectionOff()

    def set_parallel(self):
        cam = self.renderer.GetActiveCamera()
        cam.ParallelProjectionOn()

    def _handler_mousewheel(self, event):
        # event.GetWheelRotation() is + or - 120 depending on
        # direction of turning.
        if event.ControlDown():
            delta = 10
        elif event.ShiftDown():
            delta = 1
        else:
            # if user is NOT doing shift / control, we pass on to the
            # default handling which will give control to the VTK
            # mousewheel handlers.
            self.rwi.OnMouseWheel(event)
            return
            
        if event.GetWheelRotation() > 0:
            self._ipw1_delta_slice(+delta)
        else:
            self._ipw1_delta_slice(-delta)

        self.render()
        self.ipws[0].InvokeEvent('InteractionEvent')

    def _ipw1_delta_slice(self, delta):
        """Move to the delta slices fw/bw, IF the IPW is currently
        aligned with one of the axes.
        """

        ipw = self.ipws[0]
        if ipw.GetPlaneOrientation() < 3:
            ci = ipw.GetSliceIndex()
            ipw.SetSliceIndex(ci + delta)

    def render(self):
        self.rwi.GetRenderWindow().Render()

    def reset_camera(self):
        self.renderer.ResetCamera()

    def reset_to_default_view(self, view_index):
        """
        @param view_index 2 for XY
        """

        if view_index == 2:
            
            cam = self.renderer.GetActiveCamera()
            # then make sure it's up is the right way
            cam.SetViewUp(0,1,0)
            # just set the X,Y of the camera equal to the X,Y of the
            # focal point.
            fp = cam.GetFocalPoint()
            cp = cam.GetPosition()
            if cp[2] < fp[2]:
                z = fp[2] + (fp[2] - cp[2])
            else:
                z = cp[2]

            cam.SetPosition(fp[0], fp[1], z)

            # first reset the camera
            self.renderer.ResetCamera()

        self.render()
        

    def set_input(self, input):
        ipw = self.ipws[0]
        if input == ipw.GetInput():
            return

        if input is None:
            # remove outline actor, else this will cause errors when
            # we disable the IPWs (they call a render!)
            self.renderer.RemoveViewProp(self.outline_actor)
            self.outline_source.SetInput(None)

            self.dv_orientation_widget.set_input(None)
            for ipw in self.ipws:
                ipw.SetInput(None)
                # argh, this disable causes a render
                ipw.SetEnabled(0)


        else:
            self.outline_source.SetInput(input)
            self.renderer.AddViewProp(self.outline_actor)

            orientations = [2, 0, 1]
            active = [1, 0, 0]
            for i, ipw in enumerate(self.ipws):
                ipw.SetInput(input)
                ipw.SetPlaneOrientation(orientations[i]) # axial
                ipw.SetSliceIndex(0)
                ipw.SetEnabled(active[i])

            self.dv_orientation_widget.set_input(input)

###########################################################################





###########################################################################
# 2D:
# * vtkRectilinearWipeWidget, de-emphasize anything outside focus:
#   yellow blue inside, grey outside
# * IPW with yellow-blue difference inside focus, grey data1 outside
# 3D:
# * context gray (silhouette, data1), focus animated
# * context gray (silhouette, data2), focus difference image

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

class Data2MCM(ComparisonMode):
    """Match mode that only displays the matched data2.
    """

    def __init__(self, comedi, cfg_dict):
        self._comedi = comedi
        self._cfg = cfg_dict

        rwi,ren = comedi.get_compvis_vtk()
        self._sv = CMSliceViewer(rwi, ren)
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
            
class CheckerboardCM(ComparisonMode):
    """Comparison mode that shows a checkerboard of the two matched
    datasets.
    """

    def __init__(self, comedi, cfg_dict):
        self._comedi = comedi
        self._cfg = cfg_dict
        
        rwi,ren = comedi.get_compvis_vtk()
        self._sv = CMSliceViewer(rwi, ren)
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
###########################################################################
class CoMedI(IntrospectModuleMixin, ModuleBase):
    # API methods
    def __init__(self, module_manager):
        """Standard constructor.  All DeVIDE modules have these, we do
        the required setup actions.
        """

        # we record the setting here, in case the user changes it
        # during the lifetime of this model, leading to different
        # states at init and shutdown.
        self.IMAGE_VIEWER = IMAGE_VIEWER

        ModuleBase.__init__(self, module_manager)

        IntrospectModuleMixin.__init__(
            self,
            {'Module (self)' : self})

        # create the view frame
        self._view_frame = module_utils.instantiate_module_view_frame(
            self, self._module_manager, 
            CoMedIFrame.CoMedIFrame)
        # change the title to something more spectacular
        self._view_frame.SetTitle('CoMedI')


        self._setup_vis()


        # hook up all event handlers
        self._bind_events()

        # make our window appear (this is a viewer after all)
        self.view()
        # all modules should toggle this once they have shown their
        # views. 
        self.view_initialised = True

        # this will cause the correct set_cam_* call to be made
        self._config.cam_parallel = False

        # setup all match modes here.  even if the user switches
        # modes, all metadata should be serialised, so that after a
        # network reload, the user can switch and will get her old
        # metadata back from a previous session.
        self._config.sstructlandmarksmm_cfg = {}

        # default match mode is the landmark thingy
        self._config.match_mode = MATCH_MODE_LANDMARK_SS
        # this will hold a binding to the current match mode that will
        # be initially setup by config_to_logic
        self.match_mode = None

        self._config.data2mcm_cfg = {}
        self._config.checkerboardcm_cfg = {}

        self._config.comparison_mode = COMPARISON_MODE_DATA2M
        self.comparison_mode = None

        # apply config information to underlying logic
        self.sync_module_logic_with_config()
        # then bring it all the way up again to the view
        self.sync_module_view_with_logic()


    def close(self):
        """Clean-up method called on all DeVIDE modules when they are
        deleted.
        """

        # get rid of match_mode
        self.match_mode.close()

        self._close_vis()
        
        # now take care of the wx window
        self._view_frame.close()
        # then shutdown our introspection mixin
        IntrospectModuleMixin.close(self)

    def get_input_descriptions(self):
        # define this as a tuple of input descriptions if you want to
        # take input data e.g. return ('vtkPolyData', 'my kind of
        # data')
        return ('Data 1', 'Data 2')

    def get_output_descriptions(self):
        # define this as a tuple of output descriptions if you want to
        # generate output data.
        return ()



    def set_input(self, idx, input_stream):
        # this gets called right before you get executed.  take the
        # input_stream and store it so that it's available during
        # execute_module()

        if idx == 0:
            self._data1_slice_viewer.set_input(input_stream)

            if input_stream is None:
                # we're done disconnecting, no syncing necessary
                # but we do need to tell the current match_mode
                # something is going on.
                self._update_mmcm()
                return

            if not self._data2_slice_viewer.get_input():
                self._data1_slice_viewer.reset_camera()
                self._data1_slice_viewer.render()

            else:
                # sync ourselves to data2
                self.sync_slice_viewers.sync_all(
                        self._data2_slice_viewer,
                        [self._data1_slice_viewer])


        if idx == 1:
            self._data2_slice_viewer.set_input(input_stream)

            if input_stream is None:
                self._update_mmcm()
                return

            if not self._data1_slice_viewer.get_input():
                self._data2_slice_viewer.reset_camera()
                self._data2_slice_viewer.render()

            else:
                self.sync_slice_viewers.sync_all(
                        self._data1_slice_viewer,
                        [self._data2_slice_viewer])



    def get_output(self, idx):
        # this can get called at any time when a consumer module wants
        # you output data.
        pass

    def execute_module(self):
        # when it's you turn to execute as part of a network
        # execution, this gets called.
        pass

    # as per usual with viewer modules, we're keeping the config up to
    # date throughout execution, so only the config_to_logic and
    # config_to_view are implemented, so that things correctly restore
    # after a deserialisation.

    def logic_to_config(self):
        pass

    def config_to_logic(self):
        # we need to be able to build up the correct MatchMode based
        # on the config.
        self._sync_mm_with_config()
        # do the same for the comparison mode
        self._sync_cm_with_config()


    def config_to_view(self):
        if self._config.cam_parallel:
            self.set_cam_parallel()
            # also make sure this is reflected in the menu
            self._view_frame.set_cam_parallel()
        else:
            self.set_cam_perspective()
            # also make sure this is reflected in the menu
            self._view_frame.set_cam_perspective()

        # now also set the correct pages in the match mode and
        # comparison mode notebooks.
        vf = self._view_frame
        cp = vf.pane_controls.window

        # ChangeSelection does not trigger the event handlers
        cp.match_mode_notebook.ChangeSelection(
                self._config.match_mode)

        cp.comparison_mode_notebook.ChangeSelection(
                self._config.comparison_mode)



    def view_to_config(self):
        pass

    def view(self):
        self._view_frame.Show()
        self._view_frame.Raise()

        # because we have an RWI involved, we have to do this
        # SafeYield, so that the window does actually appear before we
        # call the render.  If we don't do this, we get an initial
        # empty renderwindow.
        wx.SafeYield()
        self.render_all()

    # PRIVATE methods
    def _bind_events(self):
        """Bind wx events to Python callable object event handlers.
        """
        vf = self._view_frame

        vf.Bind(wx.EVT_MENU, self._handler_cam_perspective,
                id = vf.id_camera_perspective)
        vf.Bind(wx.EVT_MENU, self._handler_cam_parallel,
                id = vf.id_camera_parallel)

        vf.Bind(wx.EVT_MENU, self._handler_cam_xyzp,
                id = vf.id_camera_xyzp)


        vf.Bind(wx.EVT_MENU, self._handler_introspect,
                id = vf.id_adv_introspect)

        vf.Bind(wx.EVT_MENU, self._handler_synced,
                id = vf.id_views_synchronised)

        vf.Bind(wx.EVT_MENU, self._handler_slice2,
                id = vf.id_views_slice2)

        vf.Bind(wx.EVT_MENU, self._handler_slice3,
                id = vf.id_views_slice3)

        cp = vf.pane_controls.window
        cp.compare_button.Bind(wx.EVT_BUTTON, self._handler_compare)
        cp.update_compvis_button.Bind(wx.EVT_BUTTON,
                self._handler_update_compvis)

        cp.match_mode_notebook.Bind(
                wx.EVT_NOTEBOOK_PAGE_CHANGED,
                self._handler_mm_nbp_changed)

        cp.comparison_mode_notebook.Bind(
                wx.EVT_NOTEBOOK_PAGE_CHANGED,
                self._handler_cm_nbp_changed)

    def _close_vis(self):
        for sv in self._slice_viewers:
            sv.close()

    def _handler_cam_parallel(self, event):
        self.set_cam_parallel()

    def _handler_cam_perspective(self, event):
        self.set_cam_perspective()

    def _handler_cam_xyzp(self, event):
        self._data1_slice_viewer.reset_to_default_view(2)
        # then synchronise the rest
        self.sync_slice_viewers.sync_all(self._data1_slice_viewer)

    def _handler_cm_nbp_changed(self, evt):
        # tab indices match the constant value.
        self._config.comparison_mode = evt.GetSelection()
        self._sync_cm_with_config()
        self.comparison_mode.update_vis()

        # we have to call this skip so that wx also changes the page
        # contents.
        evt.Skip()

    def _handler_mm_nbp_changed(self, evt):
        print "hello you too"
        # we have to call this skip so wx also changes the actual tab
        # contents.
        evt.Skip()

    def _handler_compare(self, e):
        self._update_mmcm()

    def _handler_introspect(self, e):
        self.miscObjectConfigure(self._view_frame, self, 'CoMedI')

    def _handler_slice2(self, e):
        for sv in self.sync_slice_viewers.slice_viewers:
            if e.IsChecked():
                sv.activate_slice(1)
            else:
                sv.deactivate_slice(1)

    def _handler_slice3(self, e):
        for sv in self.sync_slice_viewers.slice_viewers:
            if e.IsChecked():
                sv.activate_slice(2)
            else:
                sv.deactivate_slice(2)

    def _handler_synced(self, event):
        #cb = event.GetEventObject()
        if event.IsChecked():
            if not self.sync_slice_viewers.sync:
                self.sync_slice_viewers.sync = True
                # now do the initial sync to data1
                self.sync_slice_viewers.sync_all(
                        self._data1_slice_viewer)

        else:
            self.sync_slice_viewers.sync = False

    def _handler_update_compvis(self, evt):
        self.comparison_mode.update_vis()

    def _observer_cursor(self, vtk_o, vtk_e, txt):
        """
        @param txt: Text identifier that will be prepended to the
        cursor position update in the UI.
        """
        cd =  [0,0,0,0]
        cdv = vtk_o.GetCursorData(cd)
        if not cdv:
            # we're not cursoring
            return

        c = tuple([int(i) for i in cd])
        self._view_frame.pane_controls.window.cursor_text.SetValue(
                '%s : %s = %d' % (txt, c[0:3], c[3]))

        # also store the current cursor position in an ivar, we need
        # it.  we probably need to replace this text check with
        # something else...
        if txt.startswith('d1'):
            self._data1_slice_viewer.current_index_pos = c
            w = self._data1_slice_viewer.get_world_pos(c)
            self._data1_slice_viewer.current_world_pos = w
        elif txt.startswith('d2'):
            self._data1_slice_viewer.current_index_pos = c
            w = self._data2_slice_viewer.get_world_pos(c)
            self._data2_slice_viewer.current_world_pos = w

    def _setup_vis(self):
        # setup data1 slice viewer, instrument its slice viewers with
        # observers so that the cursor information is output to the
        # GUI
        self._data1_slice_viewer = CMSliceViewer(
                self._view_frame.rwi_pane_data1.rwi,
                self._view_frame.rwi_pane_data1.renderer)
        for ipw in self._data1_slice_viewer.ipws:
            ipw.AddObserver(
                'InteractionEvent', 
                lambda o,e: self._observer_cursor(o,e,'d1') )

        # do the same for the data2 slice viewer
        self._data2_slice_viewer = CMSliceViewer(
                self._view_frame.rwi_pane_data2.rwi,
                self._view_frame.rwi_pane_data2.renderer)
        for ipw in self._data2_slice_viewer.ipws:
            ipw.AddObserver(
                'InteractionEvent', 
                lambda o,e: self._observer_cursor(o,e,'d2') )

        self._slice_viewers = [ \
                self._data1_slice_viewer,
                self._data2_slice_viewer]

        self.sync_slice_viewers = ssv = SyncSliceViewers()
        for sv in self._slice_viewers:
            ssv.add_slice_viewer(sv)

    def _sync_cm_with_config(self):
        """Synchronise comparison mode with what's specified in the
        config.  This is used by config_to_logic as well as the
        run-time comparison mode tab switching.
        """
        if self.comparison_mode:
            self.comparison_mode.close()
            self.comparison_mode = None


        if self._config.comparison_mode == COMPARISON_MODE_DATA2M:
            self.comparison_mode = Data2MCM(
                    self, self._config.data2mcm_cfg)

        elif self._config.comparison_mode == \
                COMPARISON_MODE_CHECKERBOARD:
                    self.comparison_mode = CheckerboardCM(
                            self, self._config.checkerboardcm_cfg)


    def _sync_mm_with_config(self):
        """Synchronise match mode with what's specified in the config.
        This is used by config_to_logic as well as the run-time match
        mode tab switching.
        """

        if self.match_mode:
            self.match_mode.close()
            self.match_mode = None

        if self._config.match_mode == MATCH_MODE_LANDMARK_SS:
            # we have to create a new one in anycase!  This gets
            # called if we get a brand new config given to us, too
            # much could have changed.
            #if mm.__class__.__name__ != SStructLandmarksMM.__name__:
            self.match_mode = comedi_match_modes.SStructLandmarksMM(
                        self, self._config.sstructlandmarksmm_cfg)


    def _update_mmcm(self):
        """Update the current match mode and the comparison mode.
        """

        self.match_mode.transform()
        self.comparison_mode.update_vis()

       
    # PUBLIC methods

    def get_compvis_vtk(self):
        """Return rwi and renderer used for the compvis.  Used mostly
        by the various comparison modes.
        """
        return (
                self._view_frame.rwi_pane_compvis.rwi,
                self._view_frame.rwi_pane_compvis.renderer
                )
    def get_data1(self):
        """Return data1 input.
        """
        return self._data1_slice_viewer.get_input()

    def get_data2m(self):
        """Return currently matched data2, i.e. the output of the
        current match mode.
        """
        return self.match_mode.get_output()

    def render_all(self):
        """Method that calls Render() on the embedded RenderWindow.
        Use this after having made changes to the scene.
        """
        self._view_frame.render_all()

    def set_cam_perspective(self):
        for sv in self.sync_slice_viewers.slice_viewers:
            sv.set_perspective()
            sv.render()

        self._config.cam_parallel = False

    def set_cam_parallel(self):
        for sv in self.sync_slice_viewers.slice_viewers:
            sv.set_parallel()
            sv.render()

        self._config.cam_parallel = True    



