# $Id: vtk_slice_vwr.py,v 1.49 2002/07/29 17:09:52 cpbotha Exp $

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
        self._num_orthos = 3
        # use list comprehension to create list keeping track of inputs
        self._inputs = [{'Connected' : None, 'vtkActor' : None}
                       for i in range(self._num_inputs)]
        # then the window containing the renderwindows
        self._view_frame = None
        # the render windows themselves (4, 1 x 3d and 3 x ortho)
        self._rwis = []
        self._pws = []
        # the renderers corresponding to the render windows
        self._renderers = []

        # list of dictionaries for the "Heads Up Display" overlaid on
        # each ortho view
        self._ortho_huds = []
        # list of selected points (we can make this grow or be overwritten)
        self._sel_points = []

        self._outline_source = vtk.vtkOutlineSource()
        om = vtk.vtkPolyDataMapper()
        om.SetInput(self._outline_source.GetOutput())
        self._outline_actor = vtk.vtkActor()
        self._outline_actor.SetMapper(om)
        self._cube_axes_actor2d = vtk.vtkCubeAxesActor2D()

        # list of lists of dictionaries
        # 3 element list (one per direction) of n-element lists of
        # ortho_pipelines, where n is the number of overlays,
        # where n can vary per direction
        self._ortho_pipes = [[] for i in range(self._num_orthos)]

        # axial, sagittal, coronal reslice axes
        self._InitialResliceAxes = [{'axes' : (1,0,0, 0,1,0, 0,0,1),
                                    'origin' : (0,0,0)}, # axial (xy-plane)
                                   {'axes' : (0,0,1, 0,1,0, 1,0,0),
                                    'origin' : (0,0,0)}, # sagittal (yz-plane)
                                   {'axes' : (1,0,0, 0,0,1, 0,1,0),
                                    'origin' : (0,0,0)}] # coronal (zx-plane)

        self._left_mouse_button = 0
        
        # set the whole UI up!
        self._create_window()
        
    def close(self):
        for idx in range(self._num_inputs):
            self.set_input(idx, None)
        
        del self._outline_source
        del self._outline_actor
        del self._cube_axes_actor2d
        
        if hasattr(self, '_pws'):
            del self._pws
        if hasattr(self, '_renderers'):
            del self._renderers
        if hasattr(self, '_rws'):
            del self._rwis
        if hasattr(self,'_view_frame'):
            self._view_frame.Destroy()
            del self._view_frame
        if hasattr(self, '_ortho_huds'):
            del self._ortho_huds
        if hasattr(self, '_ortho_pipes'):
            del self._ortho_pipes


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
                # check the three ortho pipelines (each consists of mult lyrs)
                for ortidx in range(len(self._ortho_pipes)):
                    # each ortidx can (by definition) only contain ONE
                    # layer with input_idx == idx; find that layer
                    pls = filter(lambda pl, idx=idx: pl['input_idx'] == idx,
                                 self._ortho_pipes[ortidx])
                    # if we find more than one, something is awfully wrong,
                    # complain...
                    if len(pls) > 1:
                        wxLogError('More than one pipeline for this ortho with'
                                   ' the same input index!  Please report.')
                        wxLog_FlushActive()
                        
                    if len(pls) > 0:
                        pl = pls[0]
                        # remove corresponding actors from renderers
                        self._renderers[0].RemoveActor(pl['vtkActor3'])
                        self._renderers[ortidx+1].RemoveActor(pl['vtkActorO'])
                        # disconnect the input (no refs hanging around)
                        pl['vtkImageReslice'].SetInput(None)

                        if len(self._ortho_pipes[ortidx]) == 1:
                            # this means this is the last pipeline, and
                            # it's going to be removed;
                            # switch off the 3DWidget, it will be
                            # reactivated if something gets added again
                            pw = self._pws[ortidx]
                            pw.Off()
                            pw.SetInteractor(None)
                            # FIXME: at removal, the planewidget sometimes
                            # leaves 3 plane actors behind (its code
                            # seems to be fine)

                        pl_idx = self._ortho_pipes[ortidx].index(pl)
                        del self._ortho_pipes[ortidx][pl_idx]

                        print "%d layers left in ortho %d" % \
                              (len(self._ortho_pipes[ortidx]), ortidx)

                if len(self._ortho_pipes[0]) == 0:
                    # this means the last of the inputs was removed
                    self._renderers[0].RemoveActor(self._outline_actor)
                    self._renderers[0].RemoveActor(self._cube_axes_actor2d)

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
                # if we already have a vtkStructuredPoints (or similar,
                # we might want to use the IsA() method later) we must check
                # the new dataset for certain requirements

                # if newly added data has the same bounds as already added
                # data, then it may be overlayed; we should make an exception
                # with single slice overlays (ouch)
                validInput = 0
                if len(self._ortho_pipes[0]) == 0:
                    # there's nothing in the first pipeline, so the data
                    # that's being added is the first
                    validInput = 1
                else:
                    ois = self._ortho_pipes[0][0]['vtkImageReslice'].GetInput()
                    input_stream.Update()
                    input_stream.ComputeBounds()
                    if input_stream.GetBounds() == ois.GetBounds():
                        validInput = 1
                    
                if not validInput:
                    raise TypeError, "You have tried to add volume data to " \
                          "the Slice Viewer which does not have the same " \
                          "dimensions as already added volume data."
                
                for i in range(self._num_orthos):
                    self._ortho_pipes[i].append(
                        {'input_idx' : idx,
                         'vtkImageReslice' : vtk.vtkImageReslice(),
                         'vtkPlaneSourceO' : vtk.vtkPlaneSource(), 
                         'vtkPlaneSource3' : vtk.vtkPlaneSource(),
                         'vtkTexture' : vtk.vtkTexture(),
                         'vtkLookupTable' : vtk.vtkWindowLevelLookupTable(),
                         'vtkActorO' : vtk.vtkActor(),
                         'vtkActor3' : vtk.vtkActor()})
                    
                    # get just added pipeline
                    cur_pipe = self._ortho_pipes[i][-1]
                    # if this is the first layer in this channel/ortho, then
                    # we have to do some initial setup stuff

                    # more setup
                    cur_pipe['vtkImageReslice'].SetOutputDimensionality(2)
                    # connect up input
                    cur_pipe['vtkImageReslice'].SetInput(input_stream)
                    #cur_pipe['vtkImageReslice'].SetAutoCropOutput(1)
                    # switch on texture interpolation
                    cur_pipe['vtkTexture'].SetInterpolate(1)
                    # connect LUT with texture
                    cur_pipe['vtkLookupTable'].SetWindow(1000)
                    cur_pipe['vtkLookupTable'].SetLevel(1000)
                    cur_pipe['vtkLookupTable'].Build()
                    cur_pipe['vtkTexture'].SetLookupTable(
                        cur_pipe['vtkLookupTable'])
                    # connect output of reslicer to texture
                    cur_pipe['vtkTexture'].SetInput(
                        cur_pipe['vtkImageReslice'].GetOutput())
                    # make sure the LUT is  going to be used
                    cur_pipe['vtkTexture'].MapColorScalarsThroughLookupTableOn()

                    # set up a plane source
                    cur_pipe['vtkPlaneSourceO'].SetXResolution(1)
                    cur_pipe['vtkPlaneSourceO'].SetYResolution(1)
                    # and connect it to a polydatamapper
                    mapper = vtk.vtkPolyDataMapper()
                    mapper.SetInput(cur_pipe['vtkPlaneSourceO'].GetOutput())
                    cur_pipe['vtkActorO'].SetMapper(mapper)
                    cur_pipe['vtkActorO'].SetTexture(cur_pipe['vtkTexture'])
                    self._renderers[i + 1].AddActor(cur_pipe['vtkActorO'])

                    cur_pipe['vtkPlaneSource3'].SetXResolution(1)
                    cur_pipe['vtkPlaneSource3'].SetYResolution(1)
                    mapper = vtk.vtkPolyDataMapper()
                    mapper.SetInput(cur_pipe['vtkPlaneSource3'].GetOutput())
                    #cur_pipe['vtkActor3'] = vtk.vtkActor()
                    cur_pipe['vtkActor3'].SetMapper(mapper)
                    cur_pipe['vtkActor3'].SetTexture(cur_pipe['vtkTexture'])
                    self._renderers[0].AddActor(cur_pipe['vtkActor3'])
                    
                    # we've connected the pipeline, now we get to do all
                    # the bells and whistles
                    self._reset_ortho_overlay(i, cur_pipe)

                # if this is the first input, create outline and cubeaxes
                if len(self._ortho_pipes[0]) == 1:
                    reslice = self._ortho_pipes[0][0]['vtkImageReslice']
                    input = reslice.GetInput()
                    input.Update()
                    ren = self._renderers[0]
                    
                    self._outline_source.SetBounds(input.GetBounds())
                    ren.AddActor(self._outline_actor)

                    self._cube_axes_actor2d.SetBounds(input.GetBounds())
                    self._cube_axes_actor2d.SetCamera(ren.GetActiveCamera())
                    ren.AddActor(self._cube_axes_actor2d)


                # after we've done all the orthos (and their corresponding
                # plains in 3d), we should probably tell the 3d renderer
                # that something is going on :)
                self._renderers[0].ResetCamera()
                self._rwis[0].Render()
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
        

    def _create_ortho_panel(self, parent):
        panel = wxPanel(parent, id=-1)

        # first create RenderWindowInteractor and pertinent elements
        self._rwis.append(wxVTKRenderWindowInteractor(panel, -1))
        self._pws.append(vtk.vtkPlaneWidget())
        o_idx = len(self._pws) - 1
        self._pws[-1].AddObserver('InteractionEvent',
                                  lambda vtk_obj, evtname, oi=o_idx, s=self:
                                  s._pw_cb(vtk_obj, oi))
        self._renderers.append(vtk.vtkRenderer())
        #self._renderers[-1].SetBackground(1,1,1)
        self._rwis[-1].GetRenderWindow().AddRenderer(self._renderers[-1])
        #istyle = vtk.vtkInteractorStyleImage()
        istyle = self._rwis[-1].GetInteractorStyle()
        print istyle.GetClassName()
        istyle.AddObserver('LeftButtonPressEvent', self._istyle_img_cb)        
        istyle.AddObserver('MouseMoveEvent', self._istyle_img_cb)
        istyle.AddObserver('LeftButtonReleaseEvent', self._istyle_img_cb)
        istyle.AddObserver('LeaveEvent', self._istyle_img_cb)
        self._rwis[-1].SetInteractorStyle(istyle)


        # then controls
        iid = wxNewId()
        ib = wxToggleButton(panel, iid, '3D Interact')

        def _ib_cb(e, ib=ib, pw=self._pws[-1]):
            pw.SetEnabled(ib.GetValue())
        
        EVT_TOGGLEBUTTON(parent, iid, _ib_cb)

        rid = wxNewId()
        rb = wxButton(panel, rid, 'Reset')

        def _rb_cb(e, s=self, o_idx=o_idx):
            for overlay_pipe in s._ortho_pipes[o_idx]:
                s._reset_ortho_overlay(o_idx, overlay_pipe )
                #s._reset_ortho_overlay(o_idx, overlay_pipe )                
            s._rwis[0].Render()

        EVT_BUTTON(parent, rid, _rb_cb)

        button_sizer = wxBoxSizer(wxHORIZONTAL)
        button_sizer.Add(ib)
        button_sizer.Add(rb)
        
        panel_sizer = wxBoxSizer(wxVERTICAL)
        panel_sizer.Add(self._rwis[-1], option=1, flag=wxEXPAND)
        panel_sizer.Add(button_sizer, flag=wxEXPAND)
                        
        panel.SetAutoLayout(true)
        panel.SetSizer(panel_sizer)
        return panel
        
    def _create_window(self):
        # create main frame, make sure that when it's closed, it merely hides
        parent_window = self._module_manager.get_module_view_parent_window()
        self._view_frame = wxFrame(parent=parent_window, id=-1,
                                   title='slice viewer')
        EVT_CLOSE(self._view_frame,
                  lambda e, s=self: s._view_frame.Show(false))


        # panel inside the frame
        panel = wxPanel(self._view_frame, id=-1)


        #
        l_panel = wxPanel(parent=panel, id=-1)

        self._spoint_listctrl = wxListCtrl(l_panel, -1, size=(320,100),
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

        
        l_sizer = wxBoxSizer(wxVERTICAL)
        l_sizer.Add(self._spoint_listctrl, option=1, flag=wxEXPAND)
        #l_sizer.Add(wxButton(l_panel, -1, 'blaaaaat'))
        l_panel.SetAutoLayout(true)
        l_panel.SetSizer(l_sizer)
        l_sizer.Fit(l_panel)

        # right split window with 3d and ortho views
        r_splitwin = wxSplitterWindow(parent=panel, id=-1,
                                      size=(640,480))
        
        # top split window with 3d and ortho view
        #########################################
        top_splitwin = wxSplitterWindow(parent=r_splitwin, id=-1)
        # 3d view
        td_panel = wxPanel(top_splitwin, id=-1)
        self._rwis.append(wxVTKRenderWindowInteractor(td_panel, -1))
        self._renderers.append(vtk.vtkRenderer())
        self._renderers[-1].SetBackground(0.5,0.5,0.5)
        self._rwis[-1].GetRenderWindow().AddRenderer(self._renderers[-1])

        pcid = wxNewId()
        pcb = wxButton(td_panel, pcid, 'Pipeline')
        EVT_BUTTON(td_panel, pcid, lambda e, pw=self._view_frame, s=self,
                   rw=self._rwis[-1].GetRenderWindow():
                   s.vtk_pipeline_configure(pw, rw))

        button_sizer = wxBoxSizer(wxHORIZONTAL)
        button_sizer.Add(pcb)

        td_panel_sizer = wxBoxSizer(wxVERTICAL)
        td_panel_sizer.Add(self._rwis[-1], option=1, flag=wxEXPAND)
        td_panel_sizer.Add(button_sizer, flag=wxEXPAND)
        td_panel.SetAutoLayout(true)
        td_panel.SetSizer(td_panel_sizer)
        # ortho view
        o0_panel = self._create_ortho_panel(top_splitwin)

        top_splitwin.SplitVertically(td_panel, o0_panel, 320)

        # bottom split window with two (2) ortho views
        ##############################################
        bottom_splitwin = wxSplitterWindow(parent=r_splitwin, id=-1)
        # second ortho
        o1_panel = self._create_ortho_panel(bottom_splitwin)
        # third ortho
        o2_panel = self._create_ortho_panel(bottom_splitwin)
        # then split the splitwin
        bottom_splitwin.SplitVertically(o1_panel, o2_panel, 320)

        # finally split the top level split win
        #######################################
        r_splitwin.SplitHorizontally(top_splitwin, bottom_splitwin, 240)

        # then make a top-level sizer
        #############################
        tl_sizer = wxBoxSizer(wxVERTICAL)
        tl_sizer.Add(r_splitwin, option=1, flag=wxEXPAND)        
        tl_sizer.Add(l_panel, option=0, flag=wxEXPAND)

        # the panel will make use of the sizer to calculate layout
        panel.SetAutoLayout(true)
        panel.SetSizer(tl_sizer)
        # tell the frame to size itself around us
        tl_sizer.Fit(self._view_frame)
        tl_sizer.SetSizeHints(self._view_frame)
        
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

    def _reset_ortho_overlay(self, ortho_idx, overlay_pipe):
        """Arrange everything for a single overlay in a single ortho view.

        This method is to be called AFTER the pertinent VTK pipeline has been
        setup.  This is here, because one often connects modules together
        before source modules have been configured, i.e. the success of this
        method is dependent on whether the source modules have been configged.
        HOWEVER: it won't die if it hasn't, just complain.

        It will configure all 3d widgets and textures and thingies, but it
        won't CREATE anything.
        """

        reslice = overlay_pipe['vtkImageReslice']

        if len(self._ortho_pipes[ortho_idx]) == 1:
            reslice.SetResliceAxesDirectionCosines(
                self._InitialResliceAxes[ortho_idx]['axes'])
            reslice.SetResliceAxesOrigin(
                self._InitialResliceAxes[ortho_idx]['origin'])
            
            # let's configure LUT for the first layer
            reslice.Update() # this doesn't always work
            # we need to do the following, else things fall apart with
            # resetting after some oblique goodness... I believe there
            # is still some whackiness in vtkImageReslice
            reslice.GetOutput().SetUpdateExtentToWholeExtent()

            input_d = reslice.GetInput()
            (dmin, dmax) = input_d.GetScalarRange()
            w = (dmax - dmin) / 2
            l = dmin + w
            overlay_pipe['vtkLookupTable'].SetWindow(w)
            overlay_pipe['vtkLookupTable'].SetLevel(l)
            overlay_pipe['vtkLookupTable'].Build()


        else:
            # if this is NOT the first layer, it  must copy the slicer
            # config of the first ortho
            ir = self._ortho_pipes[ortho_idx][0]['vtkImageReslice']
            rad = ir.GetResliceAxesDirectionCosines()
            rao = ir.GetResliceAxesOrigin()
            reslice.SetResliceAxesDirectionCosines(rad)
            reslice.SetResliceAxesOrigin(rao)

        # create and texture map the plane for ortho viewing
        self._sync_ortho_plane_with_reslice(overlay_pipe['vtkPlaneSourceO'],
                                            reslice)

        # hmmm, we'll have to see if this makes overlays work, tee hee
        # the fact that we pack it in the order of addition should yield
        # precisely what the user expects (I think)
        self._sync_3d_plane_with_reslice(overlay_pipe['vtkPlaneSource3'],
                                         reslice)

        # set up the vtkPlaneWidgets if this is the first layer
        if len(self._ortho_pipes[ortho_idx]) == 1:
            self._pws[ortho_idx].SetResolution(20)
            self._pws[ortho_idx].SetRepresentationToOutline()
            self._pws[ortho_idx].SetPlaceFactor(1)

            # we know that the reslicer has been configured, so just let
            # the planewidget follow suit
            #reslice = overlay_pipe['vtkImageReslice']

            # we pass the 0 so that UpdatePlacement() isn't called.
            self._sync_pw_with_reslice(self._pws[ortho_idx], reslice, 0)
            
            # we have to call placewidget, as that adjusts cone and
            # sphere size
            self._pws[ortho_idx].PlaceWidget()

            rwi = self._rwis[0]
            self._pws[ortho_idx].SetInteractor(rwi)

        # setup the orthogonal camera if this is the first layer
        if len(self._ortho_pipes[ortho_idx]) == 1:
            self._setup_ortho_cam(overlay_pipe, self._renderers[ortho_idx+1])

        # whee, thaaaar she goes.
        self._rwis[ortho_idx+1].Render()

    def _setup_ortho_cam(self, cur_pipe, renderer):
        # now we're going to manipulate the camera in order to achieve some
        # gluOrtho2D() goodness
        icam = renderer.GetActiveCamera()
        # set to orthographic projection
        #icam.SetParallelProjection(1);
        # set camera 10 units away, right in the centre
        icam.SetPosition(cur_pipe['vtkPlaneSourceO'].GetCenter()[0],
                         cur_pipe['vtkPlaneSourceO'].GetCenter()[1], 10);
        icam.SetFocalPoint(cur_pipe['vtkPlaneSourceO'].GetCenter());
        #icam.OrthogonalizeViewUp()
        # make sure it's the right way up
        icam.SetViewUp(0,1,0);
        # if we don't do this, the frikking plane often gets lost
        icam.SetClippingRange(1, 11);
        # we're assuming icam->WindowCenter is (0,0), then  we're effectively
        # doing this:
        # glOrtho(-aspect*height/2, aspect*height/2, -height/2, height/2, 0,11)
        #output_bounds = cur_pipe['vtkImageReslice'].GetOutput().GetBounds()
        we = cur_pipe['vtkImageReslice'].GetOutput().GetWholeExtent()
        icam.SetParallelScale((we[1] - we[0]) / 2.0)
        icam.ParallelProjectionOn()

        #icam.SetParallelScale((output_bounds[3] - output_bounds[2])/2);

    def _sync_3d_plane_with_reslice(self, plane_source, reslice):
        """Modify 3d slice plane source to agree with reslice output.

        If you've made changes to the reslicer, call this method to make sure
        the 3d slice plane source follows suit.
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

        plane_source.SetOrigin(origin)
        plane_source.SetPoint1(p1v)
        plane_source.SetPoint2(p2v)

        # end test code

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

    def _sync_ortho_plane_with_reslice(self, plane_source, reslice):
        # try and pull the data through
        reslice.Update()
        # make the plane that the texture is mapped on
        output_bounds = reslice.GetOutput().GetBounds()
        plane_source.SetOrigin(output_bounds[0],
                               output_bounds[2],
                               0)
        plane_source.SetPoint1(output_bounds[1],
                               output_bounds[2],
                               0)
        plane_source.SetPoint2(output_bounds[0],
                               output_bounds[3],
                               0)


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

    def _pw_cb(self, pw, ortho_idx):
        origin = 3 * [0]
        point1 = 3 * [0]
        point2 = 3 * [0]
        normal = 3 * [0]
        pw.GetOrigin(origin)
        pw.GetPoint1(point1)
        pw.GetPoint2(point2)
        pw.GetNormal(normal)

        # python is so beautiful it makes me want to cry

        # first calculate x vector (subtract each element of o from the
        # corresponding element in point1)
        xa = map(operator.sub, point1, origin)
        # calculate its magnitude (first square each element, then add them
        # all together, then sqrt); yes, its faster to use operator.mul and
        # xa,xa than it is to use a lambda with only one xa
        xam = reduce(operator.add, map(operator.mul, xa, xa)) ** .5
        # then normalise the x vector (divide each element by magnitude)
        xan = map(lambda e, m=xam: 1.0 * e / m, xa)
        
        # now calculate normalised y vector
        ya = map(operator.sub, point2, origin)
        yam = reduce(operator.add, map(operator.mul, ya, ya)) ** .5
        yan = map(lambda e, m=yam: 1.0 * e / m, ya)

        for cur_pipe in self._ortho_pipes[ortho_idx]:
            ir = cur_pipe['vtkImageReslice']
            ir.SetResliceAxesDirectionCosines(xan + yan + normal)
            ir.SetResliceAxesOrigin(origin)
        
            # FIMXE: if the origin "drops out" of the input volume, the output
            # extent is too small... correct by this amount perhaps?  the code
            # below doesn't work (ugh)
            # have a look at where ImageReslice transforms the inputextent;
            # I think
            # it should be messing with the resliceaxesorigin as well when
            # transforming... (or we should)

            # very important... so that image plane remains in correct
            # position relative to where the user visualises the data cube
            ir.SetOutputOrigin((0,0,0))        

            ir.Update()

            #ir.GetOutput().SetUpdateExtentToWholeExtent()

            # make sure the 3d plane moves along with us
            self._sync_3d_plane_with_reslice(cur_pipe['vtkPlaneSource3'], ir)

            # also update the pertinent ortho view
            self._sync_ortho_plane_with_reslice(cur_pipe['vtkPlaneSourceO'],
                                                ir)

        self._sync_hud_with_pwsrc_and_reslice(ortho_idx)

                                              
        
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
