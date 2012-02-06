#Hacked out of from a class contained in Charl Botha's comedi_utils.py
#Incorporated edits by by Corine Slagboom & Noeska Smit which formed part of their comedi_utils used as part of their Emphysema Viewer.
#Final version by Francois Malan (2010-2011)

from module_kits.vtk_kit.utils import DVOrientationWidget
import operator
import vtk
import wx

class OverlaySliceViewer:
    """Class for viewing 3D binary masks in a slice-view.
    Supports arbitrary number of overlays in user-definable colours.
    """

    has_active_slices = False

    def __init__(self, rwi, renderer):
        self.rwi = rwi        
        self.renderer = renderer

        istyle = vtk.vtkInteractorStyleTrackballCamera()
        rwi.SetInteractorStyle(istyle)

        # we unbind the existing mousewheel handler so it doesn't
        # interfere
        rwi.Unbind(wx.EVT_MOUSEWHEEL)
        rwi.Bind(wx.EVT_MOUSEWHEEL, self._handler_mousewheel)

        #This is a collection of 1- or 3-component image plane widgets. Each entry corresponds to a single overlay.
        self.ipw_triads = {}
        self.add_overlay(0, [0, 0, 0, 0.1]) #Almost-transparent black - for showing the pickable plane stored at id = 0.
            
        # we only set the picker on the visible IPW, else the
        # invisible IPWs block picking!
        self.picker = vtk.vtkCellPicker()
        self.picker.SetTolerance(0.005)
        self.ipw_triads[0][0].SetPicker(self.picker)

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


    def add_overlay(self, id, rgba_colour):
        """Creates and ads a new (set of) image plane widgets corresponding to a new overlay.
           id : the string id which will be used to identify this overlay for future lookups.
           rgba_colour : a length 4 vector giving the red,green,blue,opacity value for this overlay. Range = [0,1]
        """
        if self.ipw_triads.has_key(id):
            raise ValueError('The overlay id = "%s" is already in use! Cannot this id - aborting.' % id)
        else:
            new_ipw_triad = [vtk.vtkImagePlaneWidget() for _ in range(3)]
            lut = new_ipw_triad[0].GetLookupTable()
            lut.SetNumberOfTableValues(2)
            if len(self.ipw_triads) == 0:
                lut.SetTableValue(0,0,0,0,0.1)                    #Almost-transparent black - for showing the pickable plane
            else:
                lut.SetTableValue(0,0,0,0,0)                    #Transparent: for non-interfering overlay on existing layers
            lut.SetTableValue(1,rgba_colour[0],rgba_colour[1],rgba_colour[2],rgba_colour[3]) #Specified RGBA for binary "true"
            lut.Build()

            for ipw in new_ipw_triad:
                ipw.SetInteractor(self.rwi)
                ipw.SetLookupTable(lut)

            self.ipw_triads[id] = new_ipw_triad
            base_ipw_triad = self.ipw_triads[0]

            # now actually connect the sync_overlay observer
            for i,ipw in enumerate(base_ipw_triad):
                ipw.AddObserver('InteractionEvent',lambda vtk_o, vtk_e, i=i: self.observer_sync_overlay(base_ipw_triad, new_ipw_triad, i))

    #fmalan-edit based on nnsmit-edit
    def observer_sync_overlay(self, master_ipw_triad, slave_ipw_triad, ipw_idx):
        # get the primary IPW
        master_ipw = master_ipw_triad[ipw_idx]
        # get the overlay IPW
        slave_ipw = slave_ipw_triad[ipw_idx]
        # get plane geometry from primary
        o,p1,p2 = master_ipw.GetOrigin(),master_ipw.GetPoint1(),master_ipw.GetPoint2()
        # and apply to the overlay
        slave_ipw.SetOrigin(o)
        slave_ipw.SetPoint1(p1)
        slave_ipw.SetPoint2(p2)
        slave_ipw.UpdatePlacement()
    # end edit

    def close(self):
        for id in self.ipw_triads.keys():
            self.set_input(id, None)
        self.dv_orientation_widget.close()

    def activate_slice(self, id, idx):
        if idx in [1,2]:
            self.ipw_triads[id][idx].SetEnabled(1)
            self.ipw_triads[id][idx].SetPicker(self.picker)

    def deactivate_slice(self, id, idx):
        if idx in [1,2]:
            self.ipw_triads[id][idx].SetEnabled(0)
            self.ipw_triads[id][idx].SetPicker(None)

    def _get_input(self, id):
        return self.ipw_triads[id].GetInput()

    def get_world_pos(self, image_pos):
        """Given image coordinates, return the corresponding world
        position.
        """
        idata = self._get_input(0)
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
        for id in self.ipw_triads.keys():
            self.ipw_triads[id][0].InvokeEvent('InteractionEvent')

    def _ipw1_delta_slice(self, delta):
        """Move to the delta slices fw/bw, IF the IPW is currently
        aligned with one of the axes.
        """

        ipw = self.ipw_triads[0][0]
        if ipw.GetPlaneOrientation() < 3:
            ci = ipw.GetSliceIndex()
            ipw.SetSliceIndex(ci + delta)

    def render(self):
        self.rwi.GetRenderWindow().Render()
        #TODO: Check this code        
        # nnsmit edit
        # synch those overlays:

        '''
        if self.overlay_active == 1:
            for i, ipw_overlay in enumerate(self.overlay_ipws):
                self.observer_sync_overlay(self.ipw_triads, i, 0)
                self.observer_sync_overlay(self.ipw_triads, i, 1)
                self.observer_sync_overlay(self.ipw_triads, i, 2)
        '''
        # end edit


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
        
        '''
        # nnsmit edit
        # synch overlays as well:
        if self.overlay_active == 1:
            for i, ipw_overlay in enumerate(self.overlay_ipws):
                ipw_overlay.SetSliceIndex(0)
        '''

        self.render()
        
    def set_input(self, id, input):
        if self.ipw_triads.has_key(id):
            selected_ipw_triad = self.ipw_triads[id]
            if input == selected_ipw_triad[0].GetInput():
                return

            if input is None:
                ipw_triad = self.ipw_triads[id]
                for ipw in ipw_triad:
                    # argh, this disable causes a render
                    ipw.SetEnabled(0)
                    ipw.SetInput(None)

                remaining_active_slices = False
                if self.has_active_slices:                    
                    for key in self.ipw_triads:
                        if key != 0:                            
                            ipw_triad = self.ipw_triads[key]
                            for ipw in ipw_triad:
                                if ipw.GetEnabled():
                                    remaining_active_slices = True
                                    break
                            if remaining_active_slices:
                                break
                            
                    if not remaining_active_slices:
                        self.has_active_slices = False
                        self.outline_source.SetInput(None)
                        self.renderer.RemoveViewProp(self.outline_actor)
                        self.dv_orientation_widget.set_input(None)
                        base_ipw_triad = self.ipw_triads[0]
                        for i, ipw in enumerate(base_ipw_triad):
                            ipw.SetInput(None)
                            ipw.SetEnabled(0)
            else:
                orientations = [2, 0, 1]
                active = [1, 0, 0]
                if not self.has_active_slices:
                    self.outline_source.SetInput(input)
                    self.renderer.AddViewProp(self.outline_actor)
                    self.dv_orientation_widget.set_input(input)
                    base_ipw_triad = self.ipw_triads[0]
                    for i, ipw in enumerate(base_ipw_triad):
                        ipw.SetInput(input)
                        ipw.SetPlaneOrientation(orientations[i]) # axial
                        ipw.SetSliceIndex(0)
                        ipw.SetEnabled(active[i])
                    self.has_active_slices = True

                base_ipw_triad = self.ipw_triads[0]
                for i, ipw in enumerate(selected_ipw_triad):
                    ipw.SetInput(input)
                    ipw.SetPlaneOrientation(orientations[i]) # axial
                    ipw.SetSliceIndex(0)
                    ipw.SetEnabled(active[i])
                    self.observer_sync_overlay(base_ipw_triad, selected_ipw_triad, i) #sync to the current position of the base (pickable) triad
                
        else:
            raise ValueError('The overlay with id = "%s" was not found!' % id)