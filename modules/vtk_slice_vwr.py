# $Id: vtk_slice_vwr.py,v 1.53 2002/08/27 15:16:16 cpbotha Exp $

# TODO: vtkTextureMapToPlane, like thingy...

from gen_utils import log_error
from module_base import module_base, module_mixin_vtk_pipeline_config
import vtk
import vtkcpbothapython
from wxPython.wx import *
from wxPython.xrc import *
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor
import operator

# wxGTK 2.3.2.1 bugs with mouse capture (BADLY), so we disable this
try:
    WX_USE_X_CAPTURE
except NameError:
    if wxPlatform == '__WXMSW__':
        WX_USE_X_CAPTURE = 1
    else:
        WX_USE_X_CAPTURE = 0

class vtk_slice_vwr(module_base,
                    module_mixin_vtk_pipeline_config):
    
    """Slicing, dicing slice viewing class.

    This class is used as a dscas3 module.  Given vtkImageData-like input data,
    it will show 3 slices and 3 planes in a 3d scene.  PolyData objects can
    also be added.  One can interact with the 3d slices to change the slice
    orientation and position.
    """

    def __init__(self, module_manager):
        # call base constructor
        module_base.__init__(self, module_manager)
        self._num_inputs = 5
        # use list comprehension to create list keeping track of inputs
        self._inputs = [{'Connected' : None, 'vtkActor' : None}
                       for i in range(self._num_inputs)]
        # then the window containing the renderwindows
        self._view_frame = None
        # we have a single RenderWindowInteractor
        self._rwi = None
        self._ipws = []
        # the renderers corresponding to the render windows
        self._renderer = None

        # list of selected points (we can make this grow or be overwritten)
        self._sel_points = []

        self._outline_source = vtk.vtkOutlineSource()
        om = vtk.vtkPolyDataMapper()
        om.SetInput(self._outline_source.GetOutput())
        self._outline_actor = vtk.vtkActor()
        self._outline_actor.SetMapper(om)
        self._cube_axes_actor2d = vtk.vtkCubeAxesActor2D()

        self._left_mouse_button = 0
        
        # set the whole UI up!
        self._create_window()

        # make the list of imageplanewidgets
        self._ipws = [vtk.vtkImagePlaneWidget() for i in range(3)]
        
    def close(self):
        for idx in range(self._num_inputs):
            self.set_input(idx, None)
        
        del self._outline_source
        del self._outline_actor
        del self._cube_axes_actor2d
        
        if hasattr(self, '_ipws'):
            del self._ipws
        if hasattr(self, '_renderer'):
            del self._renderer
        if hasattr(self, '_rwi'):
            del self._rwi
        if hasattr(self,'_view_frame'):
            self._view_frame.Destroy()
            del self._view_frame

#################################################################
# module API methods
#################################################################

    def get_input_descriptions(self):
        # concatenate it num_inputs times (but these are shallow copies!)
        return self._num_inputs * \
               ('vtkStructuredPoints|vtkImageData|vtkPolyData',)

    def set_input(self, idx, input_stream):
        if input_stream == None:

            if self._inputs[idx]['Connected'] == 'vtkPolyData':
                self._inputs[idx]['Connected'] = None
                if self._inputs[idx]['vtkActor'] != None:
                    self._renderers[0].RemoveActor(self._inputs[idx]['vtkActor'])
                    self._inputs[idx]['vtkActor'] = None

            elif self._inputs[idx]['Connected'] == 'vtkImageData':
                self._inputs[idx]['Connected'] = None

                # by definition, we only have one set of vtkImagePlaneWidgets
                # let's disconnect them
                for ipw in self._ipws:
                    ipw.SetInput(None)
                    ipw.Off()
                    ipw.SetInteractor(None)

                self._renderer.RemoveActor(self._outline_actor)
                self._renderer.RemoveActor(self._cube_axes_actor2d)

        elif hasattr(input_stream, 'GetClassName') and \
             callable(input_stream.GetClassName):

            if input_stream.GetClassName() == 'vtkPolyData':
               
                mapper = vtk.vtkPolyDataMapper()
                mapper.SetInput(input_stream)
                self._inputs[idx]['vtkActor'] = vtk.vtkActor()
                self._inputs[idx]['vtkActor'].SetMapper(mapper)
                self._renderers[0].AddActor(self._inputs[idx]['vtkActor'])
                self._inputs[idx]['Connected'] = 'vtkPolyData'
                self._renderers[0].ResetCamera()                
                self._rwis[0].Render()
                
            elif input_stream.IsA('vtkImageData'):

                # if we already have an ImageData input, we can't take anymore
                for input in self._inputs:
                    if input['Connected'] == 'vtkImageData':
                        raise TypeError, "You have tried to add volume data " \
                              "the slice viewer which already has a " \
                              "connected volume data set.  Disconnect the " \
                              "old dataset first."

                # make sure it's current
                input_stream.Update()

                for ipw in self._ipws:
                    ipw.SetInput(input_stream)

                self._outline_source.SetBounds(input_stream.GetBounds())
                self._renderer.AddActor(self._outline_actor)
                self._cube_axes_actor2d.SetBounds(input_stream.GetBounds())
                self._cube_axes_actor2d.SetCamera(
                    self._renderer.GetActiveCamera())
                self._renderer.AddActor(self._cube_axes_actor2d)

                self._reset()

                self._renderer.ResetCamera()
                self._rwi.Render()
                self._inputs[idx]['Connected'] = 'vtkImageData'

            else:
                raise TypeError, "Wrong input type!"

        # make sure we catch any errors!
        self._module_manager.vtk_poll_error()

        
    def get_output_descriptions(self):
        # return empty tuple
        return ()
        
    def get_output(self, idx):
        raise Exception

    def view(self):
        self._view_frame.Show(true)

#################################################################
# utility methods
#################################################################

    def _add_sel_point(self, point, ortho_idx):
        # *sniff* *sob* It's unreadable, but why's it so pretty?
        # this just formats the real point
        pos_str = "%s, %s, %s" % tuple([str(round(i,1)) for i in point])
        idx = self._spoint_listctrl.InsertStringItem(0, pos_str)

        # some handy variables
        cur_pipe = self._ortho_pipes[ortho_idx]
        reslice = cur_pipe[0]['vtkImageReslice']
        input_data = reslice.GetInput()

        # calculate discrete position
        ispacing = input_data.GetSpacing()
        dpoint = tuple([int(round(i))
                        for i in map(operator.div, point, ispacing)])

        dpos_str = "%s, %s, %s" % dpoint
        self._spoint_listctrl.SetStringItem(idx, 1, dpos_str)
        

        # now find the value(s) at this point
        dtype = input_data.GetScalarType()
        dvalue = input_data.GetScalarComponentAsFloat(dpoint[0], dpoint[1],
                                                      dpoint[2], 0)
        self._spoint_listctrl.SetStringItem(idx, 2, str(dvalue))

        # add all this information to self._sel_points
        self._sel_points.append((point, dpoint, dvalue))


        # FIXME: CONTINUE HERE
        #self._ortho_huds.append({'vtkAxes' : vtk.vtkAxes(),
        #                         'axes_actor' : vtk.vtkActor()})
        #self._ortho_huds[-1]['vtkAxes'].SetOrigin(0.0,0.0,0.5)        
        #self._ortho_huds[-1]['vtkAxes'].SymmetricOn()

        #axes_mapper = vtk.vtkPolyDataMapper()
        #axes_mapper.SetInput(self._ortho_huds[-1]['vtkAxes'].GetOutput())

        #self._ortho_huds[-1]['axes_actor'].SetMapper(axes_mapper)
        #self._ortho_huds[-1]['axes_actor'].GetProperty().SetAmbient(1.0)
        #self._ortho_huds[-1]['axes_actor'].GetProperty().SetDiffuse(0.0)
        #self._ortho_huds[-1]['axes_actor'].VisibilityOff()

        #self._renderers[-1].AddActor(self._ortho_huds[-1]['axes_actor'])

        
        # also setup the HUD for this ortho_pipe
        #ob = reslice.GetOutput().GetBounds()
        #sf = ob[1] - ob[0]
        #self._ortho_huds[ortho_idx]['vtkAxes'].SetScaleFactor(sf)
        #self._ortho_huds[ortho_idx]['vtkAxes'].SetOrigin(0.0,0.0,0.5)
        
    def _create_window(self):
        # create main frame, make sure that when it's closed, it merely hides
        parent_window = self._module_manager.get_module_view_parent_window()
        self._view_frame = wxFrame(parent=parent_window, id=-1,
                                   title='slice viewer')
        EVT_CLOSE(self._view_frame,
                  lambda e, s=self: s._view_frame.Show(false))

        # panel inside the frame
        panel = wxPanel(self._view_frame, id=-1)

        # then setup the renderwindow
        # -----------------------------------------------------------------
        self._rwi = wxVTKRenderWindowInteractor(panel, -1, size=(640,480))
        self._renderer = vtk.vtkRenderer()
        self._renderer.SetBackground(0.5,0.5,0.5)
        self._rwi.GetRenderWindow().AddRenderer(self._renderer)
        

        # then the selected point list control
        # -----------------------------------------------------------------
        self._spoint_listctrl = wxListCtrl(panel, -1, size=(320,100),
                                           style=wxLC_REPORT|wxSUNKEN_BORDER|
                                           wxLC_HRULES|wxLC_VRULES)
        self._spoint_listctrl.InsertColumn(0, 'Position')
        self._spoint_listctrl.SetColumnWidth(0, 120)
        self._spoint_listctrl.InsertColumn(1, 'Discrete')
        self._spoint_listctrl.SetColumnWidth(1, 120)        
        self._spoint_listctrl.InsertColumn(2, 'Value')
        self._spoint_listctrl.SetColumnWidth(2, 80)                
        #self._spoint_listctrl.InsertStringItem(0, 'yaa')
        #self._spoint_listctrl.InsertStringItem(1, 'yaa2')        

        
        # the button control panel
        # -----------------------------------------------------------------
        pcid = wxNewId()
        pcb = wxButton(panel, pcid, 'Pipeline')
        EVT_BUTTON(panel, pcid, lambda e, pw=self._view_frame, s=self,
                   rw=self._rwi.GetRenderWindow():
                   s.vtk_pipeline_configure(pw, rw))

        rid = wxNewId()
        rb = wxButton(panel, rid, 'Reset')
        EVT_BUTTON(panel, rid, lambda e, s=self: s._reset())

        button_sizer = wxBoxSizer(wxHORIZONTAL)
        button_sizer.Add(pcb)
        button_sizer.Add(rb)

        bottom_sizer = wxBoxSizer(wxHORIZONTAL)
        bottom_sizer.Add(self._spoint_listctrl, option=1, flag=wxEXPAND)
        bottom_sizer.Add(button_sizer)

        tl_sizer = wxBoxSizer(wxVERTICAL)
        tl_sizer.Add(self._rwi, option=1, flag=wxEXPAND)
        tl_sizer.Add(bottom_sizer)

        panel.SetAutoLayout(true)
        panel.SetSizer(tl_sizer)
        tl_sizer.Fit(self._view_frame)
        #tl_sizer.SetSizeHints(self._view_frame)

        self._view_frame.Show(true)

    def _find_wxvtkrwi_by_istyle(self, istyle):
        """Find the wxVTKRenderWindowInteractor (out of self._rwis) that owns
        the given vtkInteractorStyle.

        If one uses vtkInteractorStyle::GetInteractor, one gets the vtk_object,
        and we sometimes want the python wxVTKRenderWindowInteractor to use
        some of the wx calls.
        """

        # kind of stupid, this will always iterate over the whole list :(
        frwis = [i for i in self._rwis if i.GetInteractorStyle() == istyle]
        if len(frwis) > 0:
            return frwis[0]
        else:
            return None

    def _reset(self):
        """Arrange everything for a single overlay in a single ortho view.

        This method is to be called AFTER the pertinent VTK pipeline has been
        setup.  This is here, because one often connects modules together
        before source modules have been configured, i.e. the success of this
        method is dependent on whether the source modules have been configged.
        HOWEVER: it won't die if it hasn't, just complain.

        It will configure all 3d widgets and textures and thingies, but it
        won't CREATE anything.
        """

        # FIXME: also redo axis-actors and things

        if len(self._ipws) <= 0:
            return

        # calculate default window/level once
        (dmin,dmax) = self._ipws[0].GetInput().GetScalarRange()
        iwindow = (dmax - dmin) / 2
        ilevel = dmin + iwindow

        idx = 2
        for ipw in self._ipws:
            ipw.DisplayTextOn()
            ipw.SetInteractor(self._rwi)
            ipw.SetPlaneOrientation(idx)
            idx -= 1
            ipw.SetSliceIndex(0)
            #ipw.SetPicker(some_same_picker)
            #ipw.SetKeyPressActivationValue('x')
            ipw.GetPlaneProperty().SetColor((1,0,0))
            ipw.On()

            # see if the creator of the input_data can tell
            # us something about Window/Level
            input_data_source = ipw.GetInput().GetSource()
            print input_data_source.__class__

            if hasattr(input_data_source, 'GetWindowCenter') and \
               callable(input_data_source.GetWindowCenter):
                level = input_data_source.GetWindowCenter()
            else:
                level = ilevel

            if hasattr(input_data_source, 'GetWindowWidth') and \
               callable(input_data_source.GetWindowWidth):
                window = input_data_source.GetWindowWidth()
            else:
                window = iwindow

            lut = vtk.vtkWindowLevelLookupTable()
            lut.SetWindow(window)
            lut.SetLevel(level)
            lut.Build()
            ipw.SetLookupTable(lut)


#         input_d = reslice.GetInput()
#         (dmin, dmax) = input_d.GetScalarRange()
#         w = (dmax - dmin) / 2
#         l = dmin + w
#         overlay_pipe['vtkLookupTable'].SetWindow(w)
#         overlay_pipe['vtkLookupTable'].SetLevel(l)
#         overlay_pipe['vtkLookupTable'].Build()

        # whee, thaaaar she goes.
        self._rwi.Render()

    def _setup_ortho_cam(self, plane_source, reslice_output, renderer):
        # now we're going to manipulate the camera in order to achieve some
        # gluOrtho2D() goodness
        icam = renderer.GetActiveCamera()
        # set to orthographic projection
        #icam.SetParallelProjection(1);
        # set camera 10 units away, right in the centre
        icam.SetPosition(plane_source.GetCenter()[0],
                         plane_source.GetCenter()[1], 10);
        icam.SetFocalPoint(plane_source.GetCenter());
        #icam.OrthogonalizeViewUp()
        # make sure it's the right way up
        icam.SetViewUp(0,1,0);
        # if we don't do this, the frikking plane often gets lost
        icam.SetClippingRange(1, 11);
        # we're assuming icam->WindowCenter is (0,0), then  we're effectively
        # doing this:
        # glOrtho(-aspect*height/2, aspect*height/2, -height/2, height/2, 0,11)
        #output_bounds = cur_pipe['vtkImageReslice'].GetOutput().GetBounds()
        we = reslice_output.GetWholeExtent()
        icam.SetParallelScale((we[1] - we[0]) / 2.0)
        icam.ParallelProjectionOn()

        #icam.SetParallelScale((output_bounds[3] - output_bounds[2])/2);

    def _sync_hud_with_pwsrc_and_reslice(self, ortho_idx):
        # check if we have moved onto ANY of the selection points
        # the easiest way to do this is to make use of the 3d plane
        # on which we've texture mapped; this has already been adjusted
        # by the call to _pw_cb()
        for point in self._sel_points:
            # point has the position, discrete position, and value
            # extract only the real position
            pos = point[0]
            # p - tp
            ps = self._pws[ortho_idx].GetPolyDataSource()
            pmtp = map(operator.sub, ps.GetOrigin(), pos)
            # then calculate dotproduct of p - tp and Normal
            es = map(operator.mul, pmtp, ps.GetNormal())
            dotp = reduce(operator.add, es)

            # we use only the first reslicer
            reslice = self._ortho_pipes[ortho_idx][0]['vtkImageReslice']

            # once again, this is how we transform from input to sliced
            # output, with the fricking INVERSE of the ResliceAxes()
            input_spacing = reslice.GetInput().GetSpacing()
            rai = vtk.vtkMatrix4x4()
            vtk.vtkMatrix4x4.Invert(reslice.GetResliceAxes(), rai)
            output_spacing = rai.MultiplyPoint(input_spacing + (0.0,))
            
            if abs(dotp) < abs(output_spacing[2]):
                # here we have to project the selected point onto the
                # slice plane and update the origin of the axes_actor
                # FIXME!!!
                print str(point) + " visible!"
            else:
                self._ortho_huds[ortho_idx]['axes_actor'].VisibilityOff()

    def _sync_ortho_plane_with_ipw(self, overlay_pipe, ipw):
        # try and pull the data through
        ipw.GetInput().Update()
        rout = ipw.GetResliceOutput()
        rout.Update()

        output_bounds = rout.GetBounds()
        plane_source = overlay_pipe['vtkPlaneSourceO']
        
        # we want our plane source the same as the vtkImagePlaneWidget
        # planesource, except "flat"
        v1 = 3 * [0]        
        ipw.GetVector1(v1)
        v1m = reduce(operator.add, map(operator.mul, v1, v1)) ** .5
        v2 = 3 * [0]        
        ipw.GetVector2(v2)
        v2m = reduce(operator.add, map(operator.mul, v2, v2)) ** .5

        plane_source.SetOrigin(0,0,0)
        plane_source.SetPoint1(v1m, 0, 0)
        plane_source.SetPoint2(0, v2m, 0)

        # we want our vtkTextureMapToPlane the same size as that of the
        # vtkImagePlaneWidget
        tm2p = overlay_pipe['vtkTextureMapToPlaneO']
        tm2p.SetOrigin(0,0,0)
        tm2p.SetPoint1(output_bounds[1] - output_bounds[0], 0, 0)
        tm2p.SetPoint2(0, output_bounds[3] - output_bounds[2], 0)

    def _sync_pw_with_reslice(self, pw, reslice, update_placement=1):
        """Change plane-widget to be in sync with current reslice output.

        If you've made changes to the a vtkImageReslice, you can have the
        accompanying planewidget follow suit by calling this method.  If
        update_placement is 0, PlaneWidget.UpdatePlacement() won't be called.
        Do this if you're calling _sync_pw_with_reslice BEFORE PlaceWidget().
        """
        
        reslice.Update()
        output_bounds = reslice.GetOutput().GetBounds()
        origin = reslice.GetResliceAxesOrigin()
        p1mag = output_bounds[1] - output_bounds[0]
        p2mag = output_bounds[3] - output_bounds[2]
        radc = reslice.GetResliceAxesDirectionCosines()
        p1vn = radc[0:3]
        p1v = map(lambda x, o, m=p1mag: x*m + o, p1vn, origin)
        p2vn = radc[3:6]
        p2v = map(lambda x, o, m=p2mag: x*m + o, p2vn, origin)
            
        ps = pw.GetPolyDataSource()
        ps.SetOrigin(origin)
        ps.SetPoint1(p1v)
        ps.SetPoint2(p2v)
        
        if (update_placement):
            pw.UpdatePlacement()

        
        
#################################################################
# callbacks
#################################################################

    def _istyle_img_cb(self, istyle, command_name):
        """Call-back (observer) for InteractorStyleImage.

        We keep track of left mouse button status.  If the user drags with
        the left mouse button, we change the current slice.  Because mouse
        capturing is broken in wxGTK 2.3.2.1, we can't do that...
        """

        if command_name == 'LeftButtonPressEvent':
            # only capture mouse if we're told to
            rwi = self._find_wxvtkrwi_by_istyle(istyle)            
            if WX_USE_X_CAPTURE:
                rwi.CaptureMouse()
                
            # note status of mouse button
            self._left_mouse_button = 1
            
            if rwi.GetControlKey():
                self._rw_ortho_pick_cb(rwi)
            else:
                # chain to built-in method
                istyle.OnLeftButtonDown()
            
        elif command_name == 'MouseMoveEvent':
            if self._left_mouse_button:
                rwi = self._find_wxvtkrwi_by_istyle(istyle)
                if rwi.GetShiftKey():
                    self._rw_windowlevel_cb(rwi)
                else:
                    self._rw_slice_cb(rwi)
            else:
                istyle.OnMouseMove()

        elif command_name == 'LeftButtonReleaseEvent':
            # release mouse if we captured it
            if WX_USE_X_CAPTURE:
                rwi = self._find_wxvtkrwi_by_istyle(istyle)                
                rwi.ReleaseMouse()
            # update state variable
            self._left_mouse_button = 0
            # chain to built-in event
            istyle.OnLeftButtonUp()

        elif command_name == 'LeaveEvent':
            if not WX_USE_X_CAPTURE:
                # we only let cancel the button down if we're kludging it
                # i.e. mouse capturing DOESN'T work
                self._left_mouse_button = 0
            # chain to built-in leave handler
            istyle.OnLeave()

        else:
            raise TypeError

    def _ipw_cb(self, ortho_idx):

        cur_pipe = self._ortho_pipes[ortho_idx][0]
        
        # also update the pertinent ortho view
        self._sync_ortho_plane_with_ipw(cur_pipe,
                                        self._ipws[ortho_idx])

        # we have updated all layers, so we can now call this
        self._rwis[ortho_idx + 1].Render()

    def _rw_ortho_pick_cb(self, wxvtkrwi):
        (cx,cy) = wxvtkrwi.GetEventPosition()
        r_idx = self._rwis.index(wxvtkrwi)

        # there has to be data in this pipeline before we can go on
        if len(self._ortho_pipes[r_idx - 1]):
        
            # instantiate WorldPointPicker and use it to get the World Point
            # that we've selected
            wpp = vtk.vtkWorldPointPicker()
            wpp.Pick(cx,cy,0,self._renderers[r_idx])
            (ppx,ppy,ppz) = wpp.GetPickPosition()
            # ppz will be zero too

            # now check that it's within bounds of the sliced data
            reslice = self._ortho_pipes[r_idx - 1][0]['vtkImageReslice']
            rbounds = reslice.GetOutput().GetBounds()

            if ppx >= rbounds[0] and ppx <= rbounds[1] and \
               ppy >= rbounds[2] and ppy <= rbounds[3]:

                # this is just the way that the ResliceAxes are constructed
                # here we do: inpoint = ra * pp
                ra = reslice.GetResliceAxes()
                inpoint = ra.MultiplyPoint((ppx,ppy,ppz,1))

                input_bounds = reslice.GetInput().GetBounds()
                
                # now put this point in the applicable list
                # check that the point is in the volume
                # later we'll have a multi-point mode which is when this
                # "1" conditional will be used
                if 1 and \
                   inpoint[2] >= input_bounds[4] and \
                   inpoint[2] <= input_bounds[5]:

                    self._add_sel_point(inpoint[0:3], r_idx - 1)

                    #self._ortho_huds[r_idx - 1]['vtkAxes'].SetOrigin(ppx,ppy,
                    #                                                 0.5)
                    #self._ortho_huds[r_idx - 1]['axes_actor'].VisibilityOn()

                    self._rwis[r_idx].Render()
    
    def _rw_slice_cb(self, wxvtkrwi):
        delta = wxvtkrwi.GetEventPosition()[1] - \
                wxvtkrwi.GetLastEventPosition()[1]

        r_idx = self._rwis.index(wxvtkrwi)

        if len(self._ortho_pipes[r_idx - 1]):
            # we make use of the spacing of the first layer, so there
            reslice = self._ortho_pipes[r_idx - 1][0]['vtkImageReslice']
            reslice.UpdateInformation()

            input_spacing = reslice.GetInput().GetSpacing()
            rai = vtk.vtkMatrix4x4()
            vtk.vtkMatrix4x4.Invert(reslice.GetResliceAxes(), rai)
            output_spacing = rai.MultiplyPoint(input_spacing + (0.0,))

            # modify the underlying polydatasource of the planewidget
            ps = self._pws[r_idx - 1].GetPolyDataSource()
            ps.Push(delta * output_spacing[2])
            self._pws[r_idx - 1].UpdatePlacement()

            # then call the pw callback (tee hee)
            self._pw_cb(self._pws[r_idx - 1], r_idx - 1)
            
            # render the 3d viewer
            self._rwis[0].Render()

    def _rw_windowlevel_cb(self, wxvtkrwi):
        deltax = wxvtkrwi.GetEventPosition()[0] - \
                 wxvtkrwi.GetLastEventPosition()[0]     
        
        deltay = wxvtkrwi.GetEventPosition()[1] - \
                 wxvtkrwi.GetLastEventPosition()[1]

        ortho_idx = self._rwis.index(wxvtkrwi) - 1

        for layer_pl in self._ortho_pipes[ortho_idx]:
            lut = layer_pl['vtkLookupTable']
            lut.SetLevel(lut.GetLevel() + deltay * 5.0)
            lut.SetWindow(lut.GetWindow() + deltax * 5.0)
            lut.Build()

        wxvtkrwi.GetRenderWindow().Render()
        self._rwis[0].GetRenderWindow().Render()
