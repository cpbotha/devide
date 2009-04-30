# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

# skeleton of an AUI-based viewer module
# copy and modify for your own purposes.

# set to False for 3D viewer, True for 2D image viewer
IMAGE_VIEWER = True

MATCH_MODE_LANDMARK_SS = 1

MATCH_MODE_STRINGS = [ \
        'Single structure landmarks'
        ]

COMPARISON_MODE_DATA2M = 1
COMPARISON_MODE_CHECKERBOARD = 2

# import the frame, i.e. the wx window containing everything
import CoMedIFrame
# and do a reload, so that the GUI is also updated at reloads of this
# module.
reload(CoMedIFrame)

from external.ObjectListView import ColumnDefn, EVT_CELL_EDIT_FINISHING
import math
from module_kits.misc_kit import misc_utils
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
class DVOrientationWidget:
    """Convenience class for embedding orientation widget in any
    renderwindowinteractor.  If the data has DeVIDE style orientation
    metadata, this class will show the little LRHFAP block, otherwise
    x-y-z cursor.
    """

    def __init__(self, rwi):


        self._orientation_widget = vtk.vtkOrientationMarkerWidget()
        self._orientation_widget.SetInteractor(rwi)

        # we'll use this if there is no orientation metadata
        # just a thingy with x-y-z indicators
        self._axes_actor = vtk.vtkAxesActor()

        # we'll use this if there is orientation metadata
        self._annotated_cube_actor = aca = vtk.vtkAnnotatedCubeActor()

        # configure the thing with better colours and no stupid edges 
        #aca.TextEdgesOff()
        aca.GetXMinusFaceProperty().SetColor(1,0,0)
        aca.GetXPlusFaceProperty().SetColor(1,0,0)
        aca.GetYMinusFaceProperty().SetColor(0,1,0)
        aca.GetYPlusFaceProperty().SetColor(0,1,0)
        aca.GetZMinusFaceProperty().SetColor(0,0,1)
        aca.GetZPlusFaceProperty().SetColor(0,0,1)
       

    def close(self):
        self.set_input(None)
        self._orientation_widget.SetInteractor(None)


    def set_input(self, input_data):
        if input_data is None:
            self._orientation_widget.Off()
            return

        ala = input_data.GetFieldData().GetArray('axis_labels_array')
        if ala:
            lut = list('LRPAFH')
            labels = []
            for i in range(6):
                labels.append(lut[ala.GetValue(i)])
                
            self._set_annotated_cube_actor_labels(labels)
            self._orientation_widget.Off()
            self._orientation_widget.SetOrientationMarker(
                self._annotated_cube_actor)
            self._orientation_widget.On()
            
        else:
            self._orientation_widget.Off()
            self._orientation_widget.SetOrientationMarker(
                self._axes_actor)
            self._orientation_widget.On()

    def _set_annotated_cube_actor_labels(self, labels):
        aca = self._annotated_cube_actor
        aca.SetXMinusFaceText(labels[0])
        aca.SetXPlusFaceText(labels[1])
        aca.SetYMinusFaceText(labels[2])
        aca.SetYPlusFaceText(labels[3])
        aca.SetZMinusFaceText(labels[4])
        aca.SetZPlusFaceText(labels[5])

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
class MatchMode:
    """Plugin class that takes care of the Match Mode UI panel,
    interaction for indicating matching structures, and the subsequent
    registration.
    """

    def __init__(self, comedi, config_dict):
        raise NotImplementedError

    def close(self):
        """De-init everything.

        it's important that you de-init everything (including event
        bindings) as close() is called many times during normal
        application use.  Each time the user changes the match mode
        tab, the previous match mode is completely de-initialised.
        """
        raise NotImplementedError

    def get_output(self):
        """Return the transformed data2.  Returns None if this is not
        possible, due to the lack of input data for example.  Call
        after having called transform.
        """
        raise NotImplementedError

    def transform(self):
        """After calling this method, the output will be available and
        ready.
        """
        raise NotImplementedError

###########################################################################
class Landmark:
    def __init__(self, name, world_pos, ren):
        # we'll use this to create new actors.
        self.ren = ren

        self._create_actors()

        self.set_name(name)
        self.set_world_pos(world_pos)
       
    def close(self):
        self.ren.RemoveViewProp(self.c3da)
        self.ren.RemoveViewProp(self.ca)

    def _create_actors(self):

        # 1. create really small 3D cursor to place at relevant point
        d = 2 # 2 mm dimension 
        cs = vtk.vtkCursor3D()
        cs.AllOff()
        cs.AxesOn()
        cs.SetModelBounds(-d, +d, -d, +d, -d, +d)
        cs.SetFocalPoint(0,0,0)

        m = vtk.vtkPolyDataMapper()
        m.SetInput(cs.GetOutput())

        self.c3da = vtk.vtkActor()
        self.c3da.SetPickable(0)
        self.c3da.SetMapper(m)

        self.ren.AddActor(self.c3da)

        # 2. create caption actor with label
        ca = vtk.vtkCaptionActor2D()
        ca.GetProperty().SetColor(1,1,0)
        tp = ca.GetCaptionTextProperty()
        tp.SetColor(1,1,0)
        tp.ShadowOff()
        ca.SetPickable(0)
        ca.SetAttachmentPoint(0,0,0) # we'll move this later
        ca.SetPosition(25,10)
        ca.BorderOff()
        ca.SetWidth(0.3)
        ca.SetHeight(0.04)

        # this will be changed at the first property set
        ca.SetCaption('.')

        self.ca = ca
        self.ren.AddActor(ca)


    def get_world_pos_str(self):
        return '%.2f, %.2f, %.2f' % tuple(self.world_pos)

    def get_world_pos(self):
        return self._world_pos

    def set_world_pos(self, world_pos):
        self.c3da.SetPosition(world_pos)
        self.ca.SetAttachmentPoint(world_pos)

        self._world_pos = world_pos

    # why have I not been doing this forever?
    world_pos = property(get_world_pos, set_world_pos)

    def get_name(self):
        """Test doc string!
        """
        return self._name

    def set_name(self, name):
        self.ca.SetCaption(name)
        self._name = name

    name = property(get_name, set_name)

###########################################################################
class LandmarkList:
    """List of landmarks that also maintains a config dictionary.
    """

    def __init__(self, config_dict, olv, ren):
        """
        @param config_list: list that we will fill with (name,
        world_pos) tuples.
        @param olv: ObjectListView that will be configured to handle
        the UI to the list.
        """

        self._config_dict = config_dict
        self.landmark_dict = {}
        self._olv = olv
        self._ren = ren

        # there we go, sync internal state to passed config
        for name,world_pos in config_dict.items():
            self.add_landmark(world_pos, name)

        olv.Bind(EVT_CELL_EDIT_FINISHING,
                self._handler_olv_edit_finishing)

        # if you don't set valueSetter, this thing overwrites my
        # pretty property!!
        olv.SetColumns([
            ColumnDefn("Name", "left", 50, "name",
            valueSetter=self.olv_setter),
            ColumnDefn("Position", "left", 200, "get_world_pos_str",
                isSpaceFilling=True, isEditable=False)])

        olv.SetObjects(self.olv_landmark_list)

    def add_landmark(self, world_pos, name=None):
        if name is None:
            name = str(len(self.landmark_dict))

        lm = Landmark(name, world_pos, self._ren)
        self.landmark_dict[lm.name] = lm
        # set the config_dict.  cheap operation, so we do the whole
        # thing every time.
        self.update_config_dict()
        # then update the olv
        self._olv.SetObjects(self.olv_landmark_list)

    def close(self):
        self._olv.Unbind(EVT_CELL_EDIT_FINISHING)
        [lm.close() for lm in self.landmark_dict.values()]

    def _get_olv_landmark_list(self):
        """Returns list of Landmark objects, sorted by name.  This is
        given to the ObjectListView.
        """
        ld = self.landmark_dict
        keys,values = ld.keys(),ld.values()
        keys.sort()
        return [ld[key] for key in keys]

    olv_landmark_list = property(_get_olv_landmark_list)

    def _handler_olv_edit_finishing(self, evt):
        """This can get called only for "name" column edits, nothing
        else.
        """
        if evt.cellValue == evt.rowModel.name:
            # we don't care, name stays the same
            return

        if len(evt.cellValue) > 0 and \
                evt.cellValue not in self.landmark_dict:
                    # unique value, go ahead and change
                    # our olv_setter will be called at the right
                    # moment
                    return

        # else we veto this change
        # message box?!
        evt.Veto()

    def olv_setter(self, lm_object, new_name):
        # delete the old binding from the dictionary
        del self.landmark_dict[lm_object.name]
        # change the name in the object
        # ARGH!  why does this setting clobber the property?!
        #lm_object.name = new_name
        lm_object.set_name(new_name)
        # insert it at its correct spot
        self.landmark_dict[new_name] = lm_object
        # update the config dict
        self.update_config_dict()

    def remove_landmarks(self, names_list):
        for name in names_list:
            # get the landmark
            lm = self.landmark_dict[name]
            # de-init the landmark
            lm.close()
            # remove it from the dictionary
            del self.landmark_dict[name]

        # finally update the config dictionary
        self.update_config_dict()
        # then tell the olv about the changed situation
        self._olv.SetObjects(self.olv_landmark_list)

    def move_landmark(self, name, world_pos):
        lm = self.landmark_dict[name]
        #lm.world_pos = world_pos
        lm.set_world_pos(world_pos)
        self.update_config_dict()
        self._olv.SetObjects(self.olv_landmark_list)

    def update_config_dict(self):
        # re-init the whole thing; note that we don't re-assign, that
        # would just bind to a new dictionary and not modify the
        # passed one.
        self._config_dict.clear()
        for key,value in self.landmark_dict.items():
            self._config_dict[key] = value.world_pos


###########################################################################
class SStructLandmarksMM(MatchMode):
    """Class representing simple landmark-transform between two sets
    of points.
    """
    def __init__(self, comedi, config_dict):
        """
        @param comedi: Instance of comedi that will be used to update
        GUI and views.
        @param config_dict: This dict, part of the main module config,
        will be kept up to date throughout.
        """
        
        self._comedi = comedi
        self._cfg = config_dict

        # if we get an empty config dict, configure!
        if 'data1_landmarks' not in self._cfg:
            self._cfg['data1_landmarks'] = {}

        # do the list
        cp = comedi._view_frame.pane_controls.window
        r1 = comedi._data1_slice_viewer.renderer
        self._data1_landmarks = \
                LandmarkList(
                        self._cfg['data1_landmarks'], 
                        cp.data1_landmarks_olv, r1)

        if 'data2_landmarks' not in self._cfg:
            self._cfg['data2_landmarks'] = {}


        r2 = comedi._data2_slice_viewer.renderer
        self._data2_landmarks = \
                LandmarkList(
                        self._cfg['data2_landmarks'],
                        cp.data2_landmarks_olv, r2)

        self._setup_ui()
        self._bind_events()

        # we'll use this to store a binding to the current output
        self._output = None

        # remember, this turns out to be the transform itself
        self._landmark = vtk.vtkLandmarkTransform()
        # and this guy is going to do the work
        self._trfm = vtk.vtkImageReslice()
        self._trfm.SetInterpolationModeToCubic()
        # setup a progress message:
        module_utils.setup_vtk_object_progress(
                self._comedi, self._trfm,
                'Transforming Data 2')

    def close(self):
        self._data1_landmarks.close()
        self._data2_landmarks.close()
        self._unbind_events()

    def _add_data1_landmark(self, world_pos, name=None):
        self._data1_landmarks.add_landmark(world_pos)

    def _add_data2_landmark(self, world_pos, name=None):
        self._data2_landmarks.add_landmark(world_pos)

    def _bind_events(self):
        # remember to UNBIND all of these in _unbind_events!


        vf = self._comedi._view_frame
        cp = vf.pane_controls.window

        # bind to the add button
        cp.lm_add_button.Bind(wx.EVT_BUTTON, self._handler_add_button)


        cp.data1_landmarks_olv.Bind(
                wx.EVT_LIST_ITEM_RIGHT_CLICK,
                self._handler_solv_right_click)

        cp.data2_landmarks_olv.Bind(
                wx.EVT_LIST_ITEM_RIGHT_CLICK,
                self._handler_tolv_right_click)

    def _unbind_events(self):
        vf = self._comedi._view_frame
        cp = vf.pane_controls.window

        # bind to the add button
        cp.lm_add_button.Unbind(wx.EVT_BUTTON)

        cp.data1_landmarks_olv.Unbind(
                wx.EVT_LIST_ITEM_RIGHT_CLICK)

        cp.data2_landmarks_olv.Unbind(
                wx.EVT_LIST_ITEM_RIGHT_CLICK)


    def _handler_add_button(self, e):
        cp = self._comedi._view_frame.pane_controls.window
        v = cp.cursor_text.GetValue()
        if v.startswith('d1'):
            wp = self._comedi._data1_slice_viewer.current_world_pos
            self._add_data1_landmark(wp)
        elif v.startswith('d2'):
            wp = self._comedi._data2_slice_viewer.current_world_pos
            self._add_data2_landmark(wp)

    def _handler_delete_selected_lms(self, evt, i):
        cp = self._comedi._view_frame.pane_controls.window
        if i == 0:
            olv = cp.data1_landmarks_olv
            dobjs = olv.GetSelectedObjects()
            self._data1_landmarks.remove_landmarks(
                    [o.name for o in dobjs])
        else:
            olv = cp.data2_landmarks_olv
            dobjs = olv.GetSelectedObjects()
            self._data2_landmarks.remove_landmarks(
                    [o.name for o in dobjs])

    def _handler_move_selected_lm(self, evt, i):
        cp = self._comedi._view_frame.pane_controls.window
        v = cp.cursor_text.GetValue()
        if v.startswith('d1') and i == 0:
            # get the current world position
            wp = self._comedi._data1_slice_viewer.current_world_pos
            # get the currently selected object
            olv = cp.data1_landmarks_olv
            mobjs = olv.GetSelectedObjects()
            if mobjs:
                mobj = mobjs[0]
                # now move...
                self._data1_landmarks.move_landmark(mobj.name, wp)
                
        elif v.startswith('d2') and i == 1:
            # get the current world position
            wp = self._comedi._data2_slice_viewer.current_world_pos
            # get the currently selected object
            olv = cp.data2_landmarks_olv
            mobjs = olv.GetSelectedObjects()
            if mobjs:
                mobj = mobjs[0]
                # now move...
                self._data2_landmarks.move_landmark(mobj.name, wp)

    def _handler_solv_right_click(self, evt):
        olv = evt.GetEventObject()

        # popup that menu
        olv.PopupMenu(self._solv_menu, evt.GetPosition())

    def _handler_tolv_right_click(self, evt):
        olv = evt.GetEventObject()

        # popup that menu
        olv.PopupMenu(self._tolv_menu, evt.GetPosition())


    def _setup_ui(self):
        """Do some UI-specific setup.
        """

        vf = self._comedi._view_frame

        self._solv_menu = wx.Menu('Landmarks context menu')
        self._tolv_menu = wx.Menu('Landmarks context menu')

        # i = [0,1] for data1 and data2 landmarks respectively
        for i,m in enumerate([self._solv_menu, self._tolv_menu]):
            # move landmarks
            id_move_landmark = wx.NewId()
            m.Append(id_move_landmark,
                    "Move first selected",
                    "Move first selected landmark to current cursor.")

            vf.Bind(wx.EVT_MENU,
                    lambda e, i=i:
                    self._handler_move_selected_lm(e,i),
                    id = id_move_landmark)

            # deletion of landmarks
            id_delete_landmark = wx.NewId()
            m.Append(id_delete_landmark,
                    "Delete selected",
                    "Delete all selected landmarks.")

            vf.Bind(wx.EVT_MENU, 
                lambda e, i=i: self._handler_delete_selected_lms(e,i),
                id = id_delete_landmark)
        

    def get_output(self):
        return self._output

    def _transfer_landmarks_to_vtk(self):
        """Copy landmarks from internal vars to sets of vtkPoints,
        then set on our landmark transform filter.
        """
       
        sld = self._data1_landmarks.landmark_dict
        tld = self._data2_landmarks.landmark_dict

        names = sld.keys()

        sposs, tposs = [],[]
        for name in names:
            sposs.append(sld[name].world_pos)
            try:
                tposs.append(tld[name].world_pos)
            except KeyError:
                raise RuntimeError(
                        'Could not find data2 landmark with name %s.'
                        % (name,))

        # now transfer the two lists to vtkPoint lists
        # SOURCE:
        data1_points = vtk.vtkPoints()
        data1_points.SetNumberOfPoints(len(sposs))
        for idx,pt in enumerate(sposs):
            data1_points.SetPoint(idx, pt)


        # TARGET:
        data2_points = vtk.vtkPoints()
        data2_points.SetNumberOfPoints(len(tposs))
        for idx,pt in enumerate(tposs):
            data2_points.SetPoint(idx, pt)

        # we want to map data2 onto data1
        self._landmark.SetSourceLandmarks(data2_points)
        self._landmark.SetTargetLandmarks(data1_points)
       

    def transform(self):
        """If we have valid data and a valid set of matching
        landmarks, transform data2.

        Even if nothing has changed, this WILL perform the actual
        transformation, so don't call this method unnecessarily.
        """

        d1i = self._comedi._data1_slice_viewer.get_input()
        d2i = self._comedi._data2_slice_viewer.get_input()

        if d1i and d2i:
            # we force the landmark to do its thing
            try:
                self._transfer_landmarks_to_vtk()
            except RuntimeError, e:
                # could not transfer points
                self._output = None
                # tell the user why
                self._comedi._module_manager.log_error(
                        str(e))
            else:
                # points are set, update the transformation
                self._landmark.Update()
                # reslice transform transforms the sampling grid. 
                self._trfm.SetResliceTransform(self._landmark.GetInverse())
                self._trfm.SetInput(d2i)
                self._trfm.SetInformationInput(d1i)
                self._trfm.Update()
                self._output = self._trfm.GetOutput()

        else:
            # not enough valid inputs, so no data.
            self._output = None
            # also disconnect the transform, so we don't keep data
            # hanging around
            self._trfm.SetInput(None)


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

        cp.comparison_mode_notebook.Bind(
                wx.EVT_NOTEBOOK_PAGE_CHANGED,
                self._handler_cm_nbp_changed)

    def _handler_cam_parallel(self, event):
        self.set_cam_parallel()

    def _handler_cam_perspective(self, event):
        self.set_cam_perspective()

    def _handler_cam_xyzp(self, event):
        self._data1_slice_viewer.reset_to_default_view(2)
        # then synchronise the rest
        self.sync_slice_viewers.sync_all(self._data1_slice_viewer)

    def _handler_cm_nbp_changed(self, evt):
        print "hello"

    def _handler_compare(self, e):
        self._update_mmcm()

    def _handler_introspect(self, e):
        self.miscObjectConfigure(self._view_frame, self, 'CoMedI')

    def _handler_slice2(self, e):
        for sv in self._slice_viewers:
            if e.IsChecked():
                sv.activate_slice(1)
            else:
                sv.deactivate_slice(1)

    def _handler_slice3(self, e):
        for sv in self._slice_viewers:
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
            w = self._data1_slice_viewer.get_world_pos(c)
            self._data1_slice_viewer.current_world_pos = w
        elif txt.startswith('d2'):
            w = self._data2_slice_viewer.get_world_pos(c)
            self._data2_slice_viewer.current_world_pos = w

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
            self.match_mode = SStructLandmarksMM(
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

    def _close_vis(self):
        for sv in self._slice_viewers:
            sv.close()

