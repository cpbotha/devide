# $Id: vtk_slice_vwr.py,v 1.20 2002/05/12 17:19:04 cpbotha Exp $

from module_base import module_base
import vtk
from wxPython.wx import *
from wxPython.xrc import *
from vtk.wx.wxVTKRenderWindow import wxVTKRenderWindow

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
	self._rws = []
        # the last clicked/interacted with xy positions for every rw
	self._rw_lastxys = []
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
	
	self._create_window()
	
    def close(self):
        for idx in range(self._num_inputs):
            pass
            #self.set_input(idx, None)
	if hasattr(self, '_renderers'):
	    del self._renderers
	if hasattr(self, '_rws'):
	    del self._rws
	if hasattr(self,'_view_frame'):
	    self._view_frame.Destroy()
	    del self._view_frame
        if hasattr(self,'_ortho_pipes'):
            del self._ortho_pipes
	
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
        self._rws.append(wxVTKRenderWindow(td_panel, -1))
        self._renderers.append(vtk.vtkRenderer())
        self._rws[-1].GetRenderWindow().AddRenderer(self._renderers[-1])
        td_panel_sizer = wxBoxSizer(wxVERTICAL)
        td_panel_sizer.Add(self._rws[-1], option=1, flag=wxEXPAND)
        td_panel.SetAutoLayout(true)
        td_panel.SetSizer(td_panel_sizer)
        # ortho view
        o0_panel = wxPanel(top_splitwin, id=-1)
        self._rws.append(wxVTKRenderWindow(o0_panel, -1))
        self._renderers.append(vtk.vtkRenderer())
        self._rws[-1].GetRenderWindow().AddRenderer(self._renderers[-1])
        o0_panel_sizer = wxBoxSizer(wxVERTICAL)
        o0_panel_sizer.Add(self._rws[-1], option=1, flag=wxEXPAND)
        o0_panel.SetAutoLayout(true)
        o0_panel.SetSizer(o0_panel_sizer)
        # then split the splitwin
        top_splitwin.SplitVertically(td_panel, o0_panel, 320)

        # bottom split window with two (2) ortho views
        ##############################################
        bottom_splitwin = wxSplitterWindow(parent=tl_splitwin, id=-1)
        # first ortho
        o1_panel = wxPanel(bottom_splitwin, id=-1)
        self._rws.append(wxVTKRenderWindow(o1_panel, -1))
        self._renderers.append(vtk.vtkRenderer())
        self._rws[-1].GetRenderWindow().AddRenderer(self._renderers[-1])
        o1_panel_sizer = wxBoxSizer(wxVERTICAL)
        o1_panel_sizer.Add(self._rws[-1], option=1, flag=wxEXPAND)
        o1_panel.SetAutoLayout(true)
        o1_panel.SetSizer(o1_panel_sizer)
        # second ortho
        o2_panel = wxPanel(bottom_splitwin, id=-1)
        self._rws.append(wxVTKRenderWindow(o2_panel, -1))
        self._renderers.append(vtk.vtkRenderer())
        self._rws[-1].GetRenderWindow().AddRenderer(self._renderers[-1])
        o2_panel_sizer = wxBoxSizer(wxVERTICAL)
        o2_panel_sizer.Add(self._rws[-1], option=1, flag=wxEXPAND)
        o2_panel.SetAutoLayout(true)
        o2_panel.SetSizer(o2_panel_sizer)
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
        

        
# 	# the 3d window
# 	self.rws.append(vtkTkRenderWidget(rws_pane.pane('top3d'),
#                                           width=600, height=200))
# 	self.rw_lastxys.append({'x' : 0, 'y' : 0})
# 	self._renderers.append(vtkRenderer())
        
# 	# add last appended renderer to last appended vtkTkRenderWidget
# 	self.rws[-1].GetRenderWindow().AddRenderer(self._renderers[-1])
# 	self.rws[-1].pack(side=TOP, fill=BOTH, expand=1) # 3d window
	
# 	# pane containing three ortho views
# 	ortho_pane = Pmw.PanedWidget(rws_pane.pane('orthos'),
#                                      orient='horizontal',
#                                      hull_width=600, hull_height=150)
# 	ortho_pane.pack(side=TOP, fill=BOTH, expand=1)
	
# 	ortho_pane.add('ortho0', size=200)
# 	ortho_pane.add('ortho1', size=200)
# 	ortho_pane.add('ortho2', size=200)	
# 	for i in range(self._num_orthos):
# 	    self.rws.append(vtkTkRenderWidget(ortho_pane.pane('ortho%d' % (i)),
#                                               width=200, height=150))
# 	    self.rw_lastxys.append({'x' : 0, 'y' : 0})	    
# 	    self._renderers.append(vtkRenderer())
# 	    # add last appended renderer to last appended vtkTkRenderWidget
# 	    self.rws[-1].GetRenderWindow().AddRenderer(self._renderers[-1])

# 	    self.rws[-1].pack(side=TOP, fill=BOTH, expand=1)
# 	    Tkinter.Button(ortho_pane.pane('ortho%d' % (i)), text='blah').\
#                                                      pack(side=TOP)
	    
# 	rws_pane.pack(side=TOP, fill=BOTH, expand=1)

        self._view_frame.Show(true)
	
# 	# bind event handlers
# 	for rw in self.rws[1:]:
# 	    # we need to keep track of a last mouse activity
# 	    rw.bind('<Any-ButtonPress>', lambda e,s=self,rw=rw:
#                     s.rw_starti_cb(e.x,e.y,rw))
# 	    rw.bind('<Any-ButtonRelease>', lambda e,s=self,rw=rw:
#                     s.rw_endi_cb(e.x,e.y,rw))
# 	    # we're going to use this to change current slice
# 	    rw.bind('<B1-Motion>', lambda e,s=self,rw=rw:
#                     s.rw_slice_cb(e.x,e.y,rw))


    def get_input_descriptions(self):
	# concatenate it num_inputs times (but these are shallow copies!)
	return self._num_inputs * \
               ('vtkStructuredPoints|vtkImageData|vtkPolyData',)
    
    def setup_ortho_plane(self, cur_pipe):
	# try and pull the data through
	cur_pipe['vtkImageReslice'].Update()
	# make the plane that the texture is mapped on
	output_bounds = cur_pipe['vtkImageReslice'].GetOutput().GetBounds()
	cur_pipe['vtkPlaneSourceO'].SetOrigin(output_bounds[0],
                                              output_bounds[2], 0)
	cur_pipe['vtkPlaneSourceO'].SetPoint1(output_bounds[1],
                                              output_bounds[2], 0)
	cur_pipe['vtkPlaneSourceO'].SetPoint2(output_bounds[0],
                                              output_bounds[3], 0)

    def update_3d_plane(self, cur_pipe, output_z=0):
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

	
    def setup_camera(self, cur_pipe, renderer):
	# now we're going to manipulate the camera in order to achieve some
        # gluOrtho2D() goodness
	icam = renderer.GetActiveCamera()
	# set to orthographic projection
	#icam.SetParallelProjection(1);
	# set camera 10 units away, right in the centre
	#icam.SetPosition(cur_pipe['vtkPlaneSourceO'].GetCenter()[0],
        #                 cur_pipe['vtkPlaneSourceO'].GetCenter()[1], 10);
	#icam.SetFocalPoint(cur_pipe['vtkPlaneSourceO'].GetCenter());
	# make sure it's the right way up
	#icam.SetViewUp(0,1,0);
	#icam.SetClippingRange(1, 11);
	# we're assuming icam->WindowCenter is (0,0), then  we're effectively
        # doing this:
	# glOrtho(-aspect*height/2, aspect*height/2, -height/2, height/2, 0,11)
	#output_bounds = cur_pipe['vtkImageReslice'].GetOutput().GetBounds()

        rsz = renderer.GetRenderWindow().GetSize()
        icam.SetParallelScale(rsz[0] / 2.0)
        icam.ParallelProjectionOn()

	#icam.SetParallelScale((output_bounds[3] - output_bounds[2])/2);
	
    
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
                    # find all layers in THIS ortho pipeline with correct input_idx
                    layer_pl_indices = []
                    for layer_pl in self._ortho_pipes[ortidx]:
                        if layer_pl['input_idx'] == idx:
                            # remove corresponding actors from renderers
                            self._renderers[0].RemoveActor(layer_pl['vtkActor3'])
                            self._renderers[ortidx+1].RemoveActor(layer_pl['vtkActorO'])
                            # disconnect the input (no refs hanging around)
                            layer_pl['vtkImageReslice'].SetInput(None)
                            layer_pl_indices.append(self._ortho_pipes[ortidx].index(layer_pl))
                        if len(layer_pl_indices) > 0:
                            # make sure the indices are in ascending order
                            layer_pl_indices.sort()
                            # swap
                            layer_pl_indices.reverse()
                            # then delete the elements at these indices
                            for i in layer_pl_indices:
                                # nuke the whole dictionary
                                del self._ortho_pipes[ortidx][i]

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
                    if len(self._ortho_pipes[i]) == 1:
                        cur_pipe['vtkImageReslice'].SetResliceAxesDirectionCosines(
                            self._InitialResliceAxes[i]['axes'])
                        cur_pipe['vtkImageReslice'].SetResliceAxesOrigin(
                            self._InitialResliceAxes[i]['origin'])
                        some_trans = vtk.vtkTransform()
                        some_trans.RotateWXYZ(-50,1,1,1)
                        new_matrix = vtk.vtkMatrix4x4()
                        vtk.vtkMatrix4x4.Multiply4x4(some_trans.GetMatrix(),
                                                 cur_pipe['vtkImageReslice'].
                                                 GetResliceAxes(), new_matrix)
                        #cur_pipe['vtkImageReslice'].SetResliceAxes(new_matrix)

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
		    
		    self.setup_ortho_plane(cur_pipe)
                    self.update_3d_plane(cur_pipe, 0)
		    if len(self._ortho_pipes[i]) == 1:
			self.setup_camera(cur_pipe, self._renderers[i+1])
                        isi = vtk.vtkInteractorStyleImage()
                        rwi = self._renderers[i+1].GetRenderWindowInteractor()
                        rwi.SetInteractorStyle(isi)
                        
                    self._renderers[0].ResetCamera()
                self._inputs[idx]['Connected'] = 'vtkStructuredPoints'

	    else:
		raise TypeError, "Wrong input type!"

	
    def get_output_descriptions(self):
	# return empty tuple
	return ()
	
    def get_output(self, idx):
	raise Exception

    def view(self):
	self.rw_window.deiconify()
    
    def rw_starti_cb(self, x, y, rw):
	rw.StartMotion(x,y)
	self.rw_lastxys[self.rws.index(rw)] = {'x' : x, 'y' : y}
	
    def rw_endi_cb(self, x, y, rw):
	rw.EndMotion(x,y)
	self.rw_lastxys[self.rws.index(rw)] = {'x' : x, 'y' : y}
	
    def rw_slice_cb(self, x, y, rw):
	r_idx = self.rws.index(rw)
	
	delta = y - self.rw_lastxys[r_idx]['y']
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
            self.update_3d_plane(layer_pl, o_ra_origin[2])

            # invert the ResliceAxes
            rm = vtkMatrix4x4()
            vtkMatrix4x4.Invert(reslice.GetResliceAxes(), rm)
            # transform our new origin back to the input
            new_ResliceAxesOrigin = rm.MultiplyPoint(o_ra_origin)[0:3]
            # and set it up!
            reslice.SetResliceAxesOrigin(new_ResliceAxesOrigin)

	# at the end
	self.rw_lastxys[r_idx] = {'x' : x, 'y' : y}
        # render the pertinent orth
	rw.Render()
        # render the 3d viewer
        self.rws[0].Render()

	
