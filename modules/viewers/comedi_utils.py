# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

from module_kits.vtk_kit.utils import DVOrientationWidget
import operator
import vtk
import wx

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

