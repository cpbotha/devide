# $Id: vtk_slice_vwr.py,v 1.27 2002/05/15 14:06:47 cpbotha Exp $

from gen_utils import log_error
from module_base import module_base
import vtk
from wxPython.wx import *
from wxPython.xrc import *
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor

# wxGTK 2.3.2.1 bugs with mouse capture (BADLY), so we disable this
try:
    WX_USE_X_CAPTURE
except NameError:
    if wxPlatform == '__WXMSW__':
        WX_USE_X_CAPTURE = 1
    else:
        WX_USE_X_CAPTURE = 0

class vtk_slice_vwr(module_base):

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
        if hasattr(self, '_pws'):
            del self._pws
	if hasattr(self, '_renderers'):
	    del self._renderers
	if hasattr(self, '_rws'):
	    del self._rwis
	if hasattr(self,'_view_frame'):
	    self._view_frame.Destroy()
	    del self._view_frame
        if hasattr(self,'_ortho_pipes'):
            del self._ortho_pipes

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

    def _istyle_img_cb(self, istyle, command_name):
        """Call-back (observer) for InteractorStyleImage.

        We keep track of left mouse button status.  If the user drags with
        the left mouse button, we change the current slice.  Because mouse
        capturing is broken in wxGTK 2.3.2.1, we can't do that.
        """

        if command_name == 'LeftButtonPressEvent':
            # only capture mouse if we're told to
            if WX_USE_X_CAPTURE:
                rwi = self._find_wxvtkrwi_by_istyle(istyle)
                rwi.CaptureMouse()
            # note status of mouse button
            self._left_mouse_button = 1
            # chain to built-in method
            istyle.OnLeftButtonDown()
            
        elif command_name == 'MouseMoveEvent':
            if self._left_mouse_button:
                rwi = self._find_wxvtkrwi_by_istyle(istyle)                
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
            

    def _create_ortho_panel(self, parent):
        panel = wxPanel(parent, id=-1)
        self._rwis.append(wxVTKRenderWindowInteractor(panel, -1))
        self._pws.append(vtk.vtkPlaneWidget())        
        self._renderers.append(vtk.vtkRenderer())
        self._rwis[-1].GetRenderWindow().AddRenderer(self._renderers[-1])
        #istyle = vtk.vtkInteractorStyleTrackballCamera()
        istyle = vtk.vtkInteractorStyleImage()
        istyle.AddObserver('LeftButtonPressEvent', self._istyle_img_cb)        
        istyle.AddObserver('MouseMoveEvent', self._istyle_img_cb)
        istyle.AddObserver('LeftButtonReleaseEvent', self._istyle_img_cb)
        istyle.AddObserver('LeaveEvent', self._istyle_img_cb)
        self._rwis[-1].SetInteractorStyle(istyle)
        panel_sizer = wxBoxSizer(wxVERTICAL)
        panel_sizer.Add(self._rwis[-1], option=1, flag=wxEXPAND)
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

        # top level split window
        tl_splitwin = wxSplitterWindow(parent=panel, id=-1, size=(640,480))
        
        # top split window with 3d and ortho view
        #########################################
        top_splitwin = wxSplitterWindow(parent=tl_splitwin, id=-1)
        # 3d view
        td_panel = wxPanel(top_splitwin, id=-1)
        self._rwis.append(wxVTKRenderWindowInteractor(td_panel, -1))
        self._renderers.append(vtk.vtkRenderer())
        self._rwis[-1].GetRenderWindow().AddRenderer(self._renderers[-1])
        td_panel_sizer = wxBoxSizer(wxVERTICAL)
        td_panel_sizer.Add(self._rwis[-1], option=1, flag=wxEXPAND)
        td_panel.SetAutoLayout(true)
        td_panel.SetSizer(td_panel_sizer)
        # ortho view
        o0_panel = self._create_ortho_panel(top_splitwin)

        top_splitwin.SplitVertically(td_panel, o0_panel, 320)

        # bottom split window with two (2) ortho views
        ##############################################
        bottom_splitwin = wxSplitterWindow(parent=tl_splitwin, id=-1)
        # second ortho
        o1_panel = self._create_ortho_panel(bottom_splitwin)
        # third ortho
        o2_panel = self._create_ortho_panel(bottom_splitwin)
        # then split the splitwin
        bottom_splitwin.SplitVertically(o1_panel, o2_panel, 320)

        # finally split the top level split win
        #######################################
        tl_splitwin.SplitHorizontally(top_splitwin, bottom_splitwin, 240)


        # then make a top-level sizer
        #############################
        tl_sizer = wxBoxSizer(wxVERTICAL)
        tl_sizer.Add(tl_splitwin, option=1, flag=wxEXPAND)
        # the panel will make use of the sizer to calculate layout
        panel.SetAutoLayout(true)
        panel.SetSizer(tl_sizer)
        # tell the frame to size itself around us
        tl_sizer.Fit(self._view_frame)
        tl_sizer.SetSizeHints(self._view_frame)
        
        self._view_frame.Show(true)
	

    def get_input_descriptions(self):
	# concatenate it num_inputs times (but these are shallow copies!)
	return self._num_inputs * \
               ('vtkStructuredPoints|vtkImageData|vtkPolyData',)
    
    def _setup_ortho_plane(self, cur_pipe):
	# try and pull the data through
	cur_pipe['vtkImageReslice'].Update()
	# make the plane that the texture is mapped on
	output_bounds = cur_pipe['vtkImageReslice'].GetOutput().GetBounds()
	cur_pipe['vtkPlaneSourceO'].SetOrigin(output_bounds[0],
                                              output_bounds[2],
                                              0)
	cur_pipe['vtkPlaneSourceO'].SetPoint1(output_bounds[1],
                                              output_bounds[2],
                                              0)
	cur_pipe['vtkPlaneSourceO'].SetPoint2(output_bounds[0],
                                              output_bounds[3],
                                              0)

    def _update_3d_plane(self, cur_pipe, output_z=0):
        """Move texture-mapper 3d plane source so that it corresponds to the 
        passed output z coord.

        Given the ortho pipeline corresponding to a certain layer on a certain 
        input, this will perform the necessary changes so that the plane is
        placed, scaled and oriented correctly in the 3d viewer.
        """
        reslice = cur_pipe['vtkImageReslice']
        reslice.Update()
	output_bounds = cur_pipe['vtkImageReslice'].GetOutput().GetBounds()
        # invert the ResliceAxes
        rm = vtk.vtkMatrix4x4()
        vtk.vtkMatrix4x4.Invert(reslice.GetResliceAxes(), rm)
        # transform our new origin back to the input
        origin = rm.MultiplyPoint((output_bounds[0], output_bounds[2],
                                   output_z, 0))[0:3]
        point1 = rm.MultiplyPoint((output_bounds[1], output_bounds[2],
                                   output_z, 0))[0:3]
        point2 = rm.MultiplyPoint((output_bounds[0], output_bounds[3],
                                   output_z, 0))[0:3]

	cur_pipe['vtkPlaneSource3'].SetOrigin(origin)
	cur_pipe['vtkPlaneSource3'].SetPoint1(point1)
	cur_pipe['vtkPlaneSource3'].SetPoint2(point2)

	
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
	#icam.SetClippingRange(1, 11);
	# we're assuming icam->WindowCenter is (0,0), then  we're effectively
        # doing this:
	# glOrtho(-aspect*height/2, aspect*height/2, -height/2, height/2, 0,11)
	#output_bounds = cur_pipe['vtkImageReslice'].GetOutput().GetBounds()
        we = cur_pipe['vtkImageReslice'].GetOutput().GetWholeExtent()
        icam.SetParallelScale((we[1] - we[0]) / 2.0)
        icam.ParallelProjectionOn()

	#icam.SetParallelScale((output_bounds[3] - output_bounds[2])/2);

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

        if len(self._ortho_pipes[ortho_idx]) == 1:
            overlay_pipe['vtkImageReslice'].SetResliceAxesDirectionCosines(
                self._InitialResliceAxes[ortho_idx]['axes'])
            overlay_pipe['vtkImageReslice'].SetResliceAxesOrigin(
                self._InitialResliceAxes[ortho_idx]['origin'])
            #some_trans = vtk.vtkTransform()
            #some_trans.RotateWXYZ(-50,1,1,1)
            #new_matrix = vtk.vtkMatrix4x4()
            #vtk.vtkMatrix4x4.Multiply4x4(some_trans.GetMatrix(),
            #                             overlay_pipe['vtkImageReslice'].
            #                             GetResliceAxes(), new_matrix)
            #overlay_pipe['vtkImageReslice'].SetResliceAxes(new_matrix)
        else:
            # if this is NOT the first layer, it  must copy the slicer
            # config of the first ortho
            ir = self._ortho_pipes[ortho_idx][0]['vtkImageReslice']
            rad = ir.GetResliceAxesDirectionCosines()
            rao = ir.GetResliceAxesOrigin()
            overlay_pipe['vtkImageReslice'].SetResliceAxesDirectionCosines(rad)
            overlay_pipe['vtkImageReslice'].SetResliceAxesOrigin(rao)

        # create and texture map the plane for ortho viewing
        self._setup_ortho_plane(overlay_pipe)

        # FIXME:
        # we probably only want to do this for the first layer...(i.e. we
        # DON'T do overlays in 3D?)
        self._update_3d_plane(overlay_pipe, 0)

        # set up the vtkPlaneWidgets if this is the first layer
        if len(self._ortho_pipes[ortho_idx]) == 1:
            self._pws[ortho_idx].SetProp3D(overlay_pipe['vtkActor3'])
            if ortho_idx == 0:
                self._pws[ortho_idx].NormalToZAxisOn()
            elif ortho_idx == 1:
                self._pws[ortho_idx].NormalToXAxisOn()
            else:
                self._pws[ortho_idx].NormalToYAxisOn()
            self._pws[ortho_idx].SetResolution(20)
            self._pws[ortho_idx].SetRepresentationToOutline()
            self._pws[ortho_idx].SetPlaceFactor(1)
            self._pws[ortho_idx].PlaceWidget()
            rwi = self._rwis[0]
            self._pws[ortho_idx].SetInteractor(rwi)
            self._pws[ortho_idx].On()
                                 
        # setup the orthogonal camera if this is the first layer
        if len(self._ortho_pipes[ortho_idx]) == 1:
            self._setup_ortho_cam(overlay_pipe, self._renderers[ortho_idx+1])

        # whee, thaaaar she goes.
        self._rwis[ortho_idx+1].Render()
    
    def set_input(self, idx, input_stream):
        if input_stream == None:

            if self._inputs[idx]['Connected'] == 'vtkPolyData':
                self._inputs[idx]['Connected'] = None
                if self._inputs[idx]['vtkActor'] != None:
                    self._renderers[0].RemoveActor(self._inputs[idx]['vtkActor'])
                    self._inputs[idx]['vtkActor'] = None

            elif self._inputs[idx]['Connected'] == 'vtkStructuredPoints':
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

        elif hasattr(input_stream, 'GetClassName') and \
             callable(input_stream.GetClassName):
            if input_stream.GetClassName() == 'vtkPolyData':
		mapper = vtk.vtkPolyDataMapper()
		mapper.SetInput(input_stream)
		self._inputs[idx]['vtkActor'] = vtk.vtkActor()
		self._inputs[idx]['vtkActor'].SetMapper(mapper)
		self._renderers[0].AddActor(self._inputs[idx]['vtkActor'])
		self._inputs[idx]['Connected'] = 'vtkPolyData'
            elif input_stream.GetClassName() == 'vtkStructuredPoints':
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
                    # switch on texture interpolation
                    cur_pipe['vtkTexture'].SetInterpolate(1)
                    # connect LUT with texture
                    cur_pipe['vtkLookupTable'].SetWindow(1000)
                    cur_pipe['vtkLookupTable'].SetLevel(1000)
                    cur_pipe['vtkLookupTable'].Build()
                    cur_pipe['vtkTexture'].SetLookupTable(cur_pipe['vtkLookupTable'])
                    # connect output of reslicer to texture
                    cur_pipe['vtkTexture'].SetInput(cur_pipe['vtkImageReslice'].GetOutput())
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

                # after we've done all the orthos (and their corresponding
                # plains in 3d), we should probably tell the 3d renderer
                # that something is going on :)
                self._renderers[0].ResetCamera()
                self._rwis[0].Render()
                self._inputs[idx]['Connected'] = 'vtkStructuredPoints'

	    else:
		raise TypeError, "Wrong input type!"

	
    def get_output_descriptions(self):
	# return empty tuple
	return ()
	
    def get_output(self, idx):
	raise Exception

    def view(self):
	self._view_frame.Show(true)
    
    def rw_starti_cb(self, x, y, rw):
	rw.StartMotion(x,y)
	self.rw_lastxys[self.rws.index(rw)] = {'x' : x, 'y' : y}
	
    def rw_endi_cb(self, x, y, rw):
	rw.EndMotion(x,y)
	self.rw_lastxys[self.rws.index(rw)] = {'x' : x, 'y' : y}
	
    def _rw_slice_cb(self, wxvtkrwi):
        delta = wxvtkrwi.GetEventPosition()[1] - \
                wxvtkrwi.GetLastEventPosition()[1]

        r_idx = self._rwis.index(wxvtkrwi)

        for layer_pl in self._ortho_pipes[r_idx - 1]:
	    reslice = layer_pl['vtkImageReslice']
            
            # we're going to assume that origin, spacing and extent are set to
            # defaults, i.e. the output origin, spacing and extent are the ones
            # at input permuted through the transformation matrix
            reslice.UpdateInformation()

            # get the current ResliceAxesOrigin (we want to move this)
            ra_origin = reslice.GetResliceAxesOrigin()
            # see what it's on the output (so we can just move it along the Z)
            o_ra_origin = reslice.GetResliceAxes().MultiplyPoint(ra_origin +
                                                                 (0.0,))
            # translate input spacing to output
            input_spacing = reslice.GetInput().GetSpacing()
            output_spacing = reslice.GetResliceAxes().MultiplyPoint(input_spacing + (0.0,))
            # get input extent so we can translate it and find out what our
            # limits are for movement
            input_extent = reslice.GetInput().GetWholeExtent()
            p0 = (input_extent[0], input_extent[2], input_extent[4], 0.0)
            p1 = (input_extent[1], input_extent[3], input_extent[5], 0.0)
            output_p0 = reslice.GetResliceAxes().MultiplyPoint(p0)
            output_p1 = reslice.GetResliceAxes().MultiplyPoint(p1)
            zmin = min(output_p0[2],output_p1[2]) * output_spacing[2]
            zmax = max(output_p0[2],output_p1[2]) * output_spacing[2]

            # calculate new output origin
            o_ra_origin = list(o_ra_origin)
            o_ra_origin[2] += delta * output_spacing[2]

            # make sure we remain within the data
            if o_ra_origin[2] < zmin:
                o_ra_origin[2] = zmin
            elif o_ra_origin[2] > zmax:
                o_ra_origin[2] = zmax
            o_ra_origin = tuple(o_ra_origin)
            # make sure the 3d plane moves with us
            self._update_3d_plane(layer_pl, o_ra_origin[2])

            # invert the ResliceAxes
            rm = vtk.vtkMatrix4x4()
            vtk.vtkMatrix4x4.Invert(reslice.GetResliceAxes(), rm)
            # transform our new origin back to the input
            new_ResliceAxesOrigin = rm.MultiplyPoint(o_ra_origin)[0:3]
            # and set it up!
            reslice.SetResliceAxesOrigin(new_ResliceAxesOrigin)

        # render the pertinent orth
	wxvtkrwi.Render()
        # render the 3d viewer
        self._rwis[0].Render()

	
