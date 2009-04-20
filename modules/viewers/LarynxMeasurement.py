# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

import geometry
import os
import math
from module_base import ModuleBase
from module_mixins import IntrospectModuleMixin,\
        FileOpenDialogModuleMixin
import module_utils
import vtk
import vtkgdcm
import wx

MAJOR_MARKER_SIZE = 10
MINOR_MARKER_SIZE = 7

STATE_INIT = 0
STATE_IMAGE_LOADED = 1
STATE_APEX = 2 # clicked apex
STATE_LM = 3 # clicked lower middle
STATE_NORMAL_MARKERS = 4 # after first marker has been placed

class Measurement:
    filename = ''
    apex = (0,0) # in pixels
    lm = (0,0)
    # list of 2-element tuples for all other selected points
    points = []


class LarynxMeasurement(IntrospectModuleMixin, FileOpenDialogModuleMixin, ModuleBase):

    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        self._state = STATE_INIT
        self._config.filename = None

        self._current_measurement = None
        # pogo line first
        self._actors = []

        # list of pointwidgets, first is apex, second is lm, others
        # are others. :)
        self._markers = []

        self._pogo_line_source = None

        self._view_frame = None
        self._viewer = None
        self._reader = vtk.vtkJPEGReader()
        self._create_view_frame()
        self._bind_events()

        self.view()

        # all modules should toggle this once they have shown their
        # stuff.
        self.view_initialised = True

        self.config_to_logic()
        self.logic_to_config()
        self.config_to_view()


    def _bind_events(self):
        self._view_frame.start_button.Bind(
                wx.EVT_BUTTON, self._handler_start_button)

        self._view_frame.rwi.AddObserver(
                'LeftButtonPressEvent',
                self._handler_rwi_lbp)
        

    def _create_view_frame(self):
        import resources.python.larynx_measurement_frame
        reload(resources.python.larynx_measurement_frame)

        self._view_frame = module_utils.instantiate_module_view_frame(
            self, self._module_manager,
            resources.python.larynx_measurement_frame.LarynxMeasurementFrame)

        module_utils.create_standard_object_introspection(
            self, self._view_frame, self._view_frame.view_frame_panel,
            {'Module (self)' : self})

        # add the ECASH buttons
        #module_utils.create_eoca_buttons(self, self._view_frame,
        #                                self._view_frame.view_frame_panel)


        # now setup the VTK stuff
        if self._viewer is None and not self._view_frame is None:
            # vtkImageViewer() does not zoom but retains colour
            # vtkImageViewer2() does zoom but discards colour at
            # first window-level action.
            # vtkgdcm.vtkImageColorViewer() does both right!
            self._viewer = vtkgdcm.vtkImageColorViewer()
            self._viewer.SetupInteractor(self._view_frame.rwi)
            self._viewer.GetRenderer().SetBackground(0.3,0.3,0.3)
            self._set_image_viewer_dummy_input()

            pp = vtk.vtkPointPicker()
            pp.SetTolerance(0.0)
            self._view_frame.rwi.SetPicker(pp)
    


    def close(self):
        for i in range(len(self.get_input_descriptions())):
            self.set_input(i, None)

        # with this complicated de-init, we make sure that VTK is 
        # properly taken care of
        self._viewer.GetRenderer().RemoveAllViewProps()
        self._viewer.SetupInteractor(None)
        self._viewer.SetRenderer(None)
        # this finalize makes sure we don't get any strange X
        # errors when we kill the module.
        self._viewer.GetRenderWindow().Finalize()
        self._viewer.SetRenderWindow(None)
        del self._viewer
        # done with VTK de-init

       
        self._view_frame.Destroy()
        del self._view_frame

        ModuleBase.close(self)

    def get_input_descriptions(self):
        return ()

    def get_output_descriptions(self):
        return ()

    def set_input(self, idx, input_stream):
        raise RuntimeError

    def get_output(self, idx):
        raise RuntimeError

    def logic_to_config(self):
        pass

    def config_to_logic(self):
        pass

    def view_to_config(self):
        # there is no explicit apply step in this viewer module, so we
        # keep the config up to date throughout (this is common for
        # pure viewer modules)
        pass

    def config_to_view(self):
        # this will happen right after module reload / network load
        if self._config.filename is not None:
            self._start(self._config.filename)


    def view(self):
        self._view_frame.Show()
        self._view_frame.Raise()

        # we need to do this to make sure that the Show() and Raise() above
        # are actually performed.  Not doing this is what resulted in the
        # "empty renderwindow" bug after module reloading, and also in the
        # fact that shortly after module creation dummy data rendered outside
        # the module frame.
        wx.SafeYield()

        self.render()
        # so if we bring up the view after having executed the network once,
        # re-executing will not do a set_input()!  (the scheduler doesn't
        # know that the module is now dirty)  Two solutions:
        # * make module dirty when view is activated
        # * activate view at instantiation. <--- we're doing this now.
 
    def execute_module(self):
        pass

    def _add_normal_marker(self, world_pos):
        if not len(self._markers) >= 2:
            raise RuntimeError(
            'There should be 2 or more markers by now!')
    
        pw = self._add_marker(world_pos, (0,1,0), 0.005)
        self._markers.append(pw)

    def _add_pogo_line(self):
        ls = vtk.vtkLineSource()
        self._pogo_line_source = ls

        m = vtk.vtkPolyDataMapper()
        m.SetInput(ls.GetOutput())

        a = vtk.vtkActor()
        a.SetMapper(m)

        prop = a.GetProperty()
        prop.SetLineStipplePattern(0x1010)
        prop.SetLineStippleRepeatFactor(1)

        self._viewer.GetRenderer().AddActor(a)
        self._actors.append(a)

        self._update_pogo_distance()

        self.render()


    def _add_sphere(self, world_pos, radius, colour):
        ss = vtk.vtkSphereSource()
        ss.SetRadius(radius)
        m = vtk.vtkPolyDataMapper()
        m.SetInput(ss.GetOutput())
        a = vtk.vtkActor()
        a.SetMapper(m)
        a.SetPosition(world_pos)
        a.GetProperty().SetColor(colour)
        self._viewer.GetRenderer().AddActor(a)
        self.render()

    def _add_marker(self, world_pos, colour, size=0.01):
        """
        @param size: fraction of visible prop bounds diagonal.
        """

        #self._add_sphere(world_pos, MAJOR_MARKER_SIZE, (1,1,0))
        pw = vtk.vtkPointWidget()
        # we're giving it a small bounding box
        pw.TranslationModeOn()
        b = self._viewer.GetRenderer().ComputeVisiblePropBounds()
        # calculate diagonal
        dx,dy = b[1] - b[0], b[3] - b[2]
        diag = math.hypot(dx,dy)
        d = size * diag
        w = world_pos
        pwb = w[0] - d, w[0] + d, \
                w[1] - d, w[1] + d, \
                b[4], b[5]

        pw.PlaceWidget(pwb)
        pw.SetPosition(world_pos)
        pw.SetInteractor(self._view_frame.rwi)
        pw.AllOff()

        pw.GetProperty().SetColor(colour)

        pw.On()

        return pw

    def _add_apex_marker(self, world_pos):
        # this method should only be called when the list is empty!
        if self._markers:
            raise RuntimeError('Marker list is not empty!')

        self._markers.append(self._add_marker(world_pos, (1,1,0)))

        self._markers[-1].AddObserver(
                'InteractionEvent',
                self._handler_alm_ie)


    def _add_lm_marker(self, world_pos):
        if len(self._markers) != 1:
            raise RuntimeError(
            'Marker list should have only one entry!')

        self._markers.append(self._add_marker(world_pos, (0,1,1)))

        self._markers[-1].AddObserver(
                'InteractionEvent',
                self._handler_alm_ie)


    def _handler_alm_ie(self, pw=None, vtk_e=None):
        self._update_pogo_distance()
        self._update_area()


    def _handler_rwi_lbp(self, vtk_o, vtk_e):
        # we only handle this if the user is pressing shift
        if not vtk_o.GetShiftKey():
            return

        pp = vtk_o.GetPicker() # this will be our pointpicker
        x,y = vtk_o.GetEventPosition()

        #iapp = vtk.vtkImageActorPointPlacer()
        #ren = self._viewer.GetRenderer()
        #iapp.SetImageActor(our_actor)
        #iapp.ComputeWorldPosition(ren, display_pos, 3xdouble,
        #        9xdouble)


        if not pp.Pick(x,y,0,self._viewer.GetRenderer()):
            print "off image!"
        else:
            print pp.GetMapperPosition()


            # now also get WorldPos
            ren = self._viewer.GetRenderer()
            ren.SetDisplayPoint(x,y,0)
            ren.DisplayToWorld()
            w = ren.GetWorldPoint()[0:3]
            print w

            # we have a picked position and a world point, now decide
            # what to do based on our current state
            if self._state == STATE_IMAGE_LOADED:
                # put down the apex ball
                self._add_apex_marker(w)
                self._state = STATE_APEX
            elif self._state == STATE_APEX:
                # put down the LM ball
                self._add_lm_marker(w)
                self._add_pogo_line()
                self._state = STATE_LM
            elif self._state == STATE_LM:
                # now we're putting down all other markers
                self._add_normal_marker(w)
                self._state = STATE_NORMAL_MARKERS
                # now create the polydata
                #self._create_area_polydata()
                self._update_area()
            elif self._state == STATE_NORMAL_MARKERS:
                self._add_normal_marker(w)
                self._update_area()


        
    def _handler_start_button(self, evt):
        # let user pick image
        # - close down any running analysis
        # - analyze all jpg images in that dir
        # - read / initialise SQL db

        # first get filename from user
        filename = self.filename_browse(self._view_frame, 
        'Select FIRST subject image to start processing', 
        'Subject image (*.jpg)|*.jpg;*.JPG', 
        style=wx.OPEN)

        if filename:
            self._start(filename)

    def render(self):
        # if you call self._viewer.Render() here, you get the
        # VTK-window out of main window effect at startup.  So don't.
        self._view_frame.rwi.Render()

    def _reset_image_pz(self):
        """Reset the pan/zoom of the current image.
        """

        ren = self._viewer.GetRenderer()
        ren.ResetCamera()

    def _stop(self):
        # close down any running analysis
        # first remove all polydatas we might have added to the scene
        for a in self._actors:
            self._viewer.GetRenderer().RemoveViewProp(a)

        for m in self._markers:
            m.Off()
            m.SetInteractor(None)

        del self._markers[:]

        # setup dummy image input.
        self._set_image_viewer_dummy_input()
        # set state to initialised
        self._state = STATE_INIT

    def _start(self, new_filename):
        # first see if we can open the new file
        new_reader = self._open_image_file(new_filename)
        # FIXME: also check if we can open / create sqlite file

        # if so, stop previous session
        self._stop()

        # replace reader and show the image
        self._reader = new_reader
        self._viewer.SetInput(self._reader.GetOutput())

        # show the new filename in the correct image box
        self._view_frame.current_image_txt.SetValue(new_filename)
        self._config.filename = new_filename

        cm = Measurement()
        cm.filename = self._config.filename
        self._current_measurement = cm

        self._actors = []

        self._reset_image_pz()
        self.render()

        # FIXME: get new polydata ready

        self._state = STATE_IMAGE_LOADED

        
    def _set_image_viewer_dummy_input(self):
        ds = vtk.vtkImageGridSource()
        self._viewer.SetInput(ds.GetOutput())

    def _open_image_file(self, filename):
        # create a new instance of the current reader
        # to read the passed file.
        nr = self._reader.NewInstance()
        nr.SetFileName(filename)
        # FIXME: trap this error
        nr.Update()
        return nr

    def _update_pogo_distance(self):
        """Based on the first two markers, update the pogo line and
        recalculate the distance.
        """

        if len(self._markers) >= 2:
            p1,p2 = [self._markers[i].GetPosition() for i in range(2)] 
            self._pogo_line_source.SetPoint1(p1)
            self._pogo_line_source.SetPoint2(p2)

            pogo_dist = math.hypot(p2[0] - p1[0], p2[1] - p1[0])
            self._view_frame.pogo_dist_txt.SetValue('%.2f' %
                    (pogo_dist,))


    def _update_area(self):
        """Based on three or more markers in total, draw a nice
        polygon and update the total area.
        """

        if len(self._markers) >= 3:
            # start from apex, then all markers to the right of the
            # pogo line, then the lm point, then all markers to the
            # left.

            p1,p2 = [self._markers[i].GetPosition()[0:2] for i in range(2)] 

            # gradient
            #m = (p2[1] - p1[1]) / float(p2[0] - p1[0])

            n,mag,lv = geometry.normalise_line(p1,p2) 

            # get its orthogonal vector
            no = - n[1],n[0]

            pts = [self._markers[i].GetPosition()[0:2] 
                    for i in range(2, len(self._markers))]
            right_pts = []
            left_pts = []

            for p in pts:
                v = geometry.points_to_vector(p1,p) 
                # project v onto n
                v_on_n = geometry.dot(v,n) * n
                # then use that to determine the vector orthogonal on
                # n from p
                v_ortho_n = v - v_on_n
                # rl is positive for right hemisphere, negative for
                # otherwise
                rl = geometry.dot(no, v_ortho_n)
                if rl > 0:
                    right_pts.append(p)
                elif rl < 0:
                    left_pts.append(p)
                else:
                    # we ignore points on the line
                    pass

            

            



