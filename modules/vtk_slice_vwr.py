# $Id: vtk_slice_vwr.py,v 1.6 2002/03/23 00:52:53 cpbotha Exp $
from module_base import module_base
from vtkpython import *
import Tkinter
from Tkconstants import *
import Pmw
from vtkPipeline.vtkPipeline import vtkPipelineBrowser, vtkPipelineSegmentBrowser
from vtkTkRenderWidget import vtkTkRenderWidget


class vtk_slice_vwr(module_base):
    def __init__(self):
        self.num_inputs = 5
        self.num_orthos = 3
        # use list comprehension to create list keeping track of inputs
	self.inputs = [{'Connected' : 0, 'vtkActor' : None} for i in range(self.num_inputs)]
	self.rw_window = None
	self.rws = []
	self.rw_lastxys = []
	self.renderers = []

        # list of lists of dictionaries
        # 3 element list (one per direction) of n-element lists of ortho_pipelines, where n is the number of overlays,
        # where n can vary per direction
        self.ortho_pipes = [[] for i in range(self.num_orthos)]

        # axial, sagittal, coronal
        self.IntialResliceAxesDirectionCosines = [(1,0,0, 0,1,0, 0,0,1), (0,1,0, 0,0,1, 1,0,0), (1,0,0, 0,0,1, 0,-1,0)]
	
	self.create_window()
	
    def __del__(self):
	self.close()
	
    def close(self):
	if hasattr(self, 'renderers'):
	    del self.renderers
	if hasattr(self, 'rws'):
	    del self.rws
	if hasattr(self,'rw_window'):
	    self.rw_window.destroy()
	    del self.rw_window
        if hasattr(self,'ortho_pipes'):
            del self.ortho_pipes
	
    def create_window(self):
	self.rw_window = Tkinter.Toplevel(None)
	self.rw_window.title("slice viewer")
	# widthdraw hides the window, deiconify makes it appear again
	self.rw_window.protocol("WM_DELETE_WINDOW", self.rw_window.withdraw)
	
	# paned widget with two panes, one for 3d window the other for ortho views
	# default vertical (i.e. divider is horizontal line)
	# hull width and height refer to the whole thing!
	rws_pane = Pmw.PanedWidget(self.rw_window, hull_width=600, hull_height=400)
	rws_pane.add('top3d', size=200)
        rws_pane.add('orthos', size=200)	

	# the 3d window
	self.rws.append(vtkTkRenderWidget(rws_pane.pane('top3d'), width=600, height=200))
	self.rw_lastxys.append({'x' : 0, 'y' : 0}) # we're never going to use this one...
	self.renderers.append(vtkRenderer())
	# add last appended renderer to last appended vtkTkRenderWidget
	self.rws[-1].GetRenderWindow().AddRenderer(self.renderers[-1])
	self.rws[-1].pack(side=TOP, fill=BOTH, expand=1) # 3d window is at the top
	
	# pane containing three ortho views
	ortho_pane = Pmw.PanedWidget(rws_pane.pane('orthos'), orient='horizontal', hull_width=600, hull_height=150)
	ortho_pane.pack(side=TOP, fill=BOTH, expand=1)
	
	ortho_pane.add('ortho0', size=200)
	ortho_pane.add('ortho1', size=200)
	ortho_pane.add('ortho2', size=200)	
	for i in range(self.num_orthos):
	    self.rws.append(vtkTkRenderWidget(ortho_pane.pane('ortho%d' % (i)), width=200, height=150))
	    self.rw_lastxys.append({'x' : 0, 'y' : 0})	    
	    self.renderers.append(vtkRenderer())
	    # add last appended renderer to last appended vtkTkRenderWidget
	    self.rws[-1].GetRenderWindow().AddRenderer(self.renderers[-1])
	    self.rws[-1].pack(side=LEFT, fill=BOTH, expand=1)

	rws_pane.pack(side=TOP, fill=BOTH, expand=1)
	
	# bind event handlers
	for rw in self.rws[1:]:
	    # we need to keep track of a last mouse activity
	    rw.bind('<Any-ButtonPress>', lambda e,s=self,rw=rw: s.rw_starti_cb(e.x,e.y,rw))
	    rw.bind('<Any-ButtonRelease>', lambda e,s=self,rw=rw: s.rw_endi_cb(e.x,e.y,rw))
	    # we're going to use this to change current slice
	    rw.bind('<B1-Motion>', lambda e,s=self,rw=rw: s.rw_slice_cb(e.x,e.y,rw))


    def get_input_descriptions(self):
	# concatenate it num_inputs times (but these are shallow copies!)
	return self.num_inputs * ('vtkStructuredPoints|vtkImageData|vtkPolyData',)
    
    def setup_plane(self, cur_pipe):
	# try and pull the data through
	cur_pipe['vtkImageReslice'].Update()
	# make the plane that the texture is mapped on
	output_bounds = cur_pipe['vtkImageReslice'].GetOutput().GetBounds()
	cur_pipe['vtkPlaneSource'].SetOrigin(output_bounds[0], output_bounds[2], 0)
	cur_pipe['vtkPlaneSource'].SetPoint1(output_bounds[1], output_bounds[2], 0)
	cur_pipe['vtkPlaneSource'].SetPoint2(output_bounds[0], output_bounds[3], 0)
	
    def setup_camera(self, cur_pipe, renderer):
	# now we're going to manipulate the camera in order to achieve some gluOrtho2D() goodness
	icam = renderer.GetActiveCamera()
	# set to orthographic projection
	icam.SetParallelProjection(1);
	# set camera 10 units away, right in the centre
	icam.SetPosition(cur_pipe['vtkPlaneSource'].GetCenter()[0], cur_pipe['vtkPlaneSource'].GetCenter()[1], 10);
	icam.SetFocalPoint(cur_pipe['vtkPlaneSource'].GetCenter());
	# make sure it's the right way up
	icam.SetViewUp(0,1,0);
	icam.SetClippingRange(1, 11);
	# we're assuming icam->WindowCenter is (0,0), then  we're effectively doing this:
	# glOrtho(-aspect*height/2, aspect*height/2, -height/2, height/2, 0, 11)
	output_bounds = cur_pipe['vtkImageReslice'].GetOutput().GetBounds()
	icam.SetParallelScale((output_bounds[3] - output_bounds[2])/2);
	
    
    def set_input(self, idx, input_stream):
        if input_stream == None:
            print "implement disconnect"
        elif hasattr(input_stream, 'GetClassName') and callable(input_stream.GetClassName):
            print input_stream.GetClassName()
            if input_stream.GetClassName() == 'vtkPolyData':
		mapper = vtkPolyDataMapper()
		mapper.SetInput(input_stream)
		self.inputs[idx]['vtkActor'] = vtkActor()
		self.inputs[idx]['vtkActor'].SetMapper(mapper)
		self.renderers[0].AddActor(self.inputs[idx]['vtkActor'])
		self.inputs[idx]['Connected'] = 1
            elif input_stream.GetClassName() == 'vtkStructuredPoints':
                # find the maximum number of layers
                #max([len(i) for i in self.ortho_pipes])
                for i in range(self.num_orthos):
                    self.ortho_pipes[i].append({'vtkImageReslice' : vtkImageReslice(), 'vtkPlaneSource' : vtkPlaneSource(), 
                                                             'vtkTexture' : vtkTexture(), 'vtkLookupTable' : vtkWindowLevelLookupTable(),
                                                             'vtkActor' : vtkActor()})
                    # get just added pipeline
                    cur_pipe = self.ortho_pipes[i][-1]
                    # if this is the first layer in this channel/ortho, then we have to do some initial setup stuff
                    if len(self.ortho_pipes[i]) == 1:
                        cur_pipe['vtkImageReslice'].SetResliceAxesDirectionCosines(self.IntialResliceAxesDirectionCosines[i])
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
                    cur_pipe['vtkPlaneSource'].SetXResolution(1)
                    cur_pipe['vtkPlaneSource'].SetYResolution(1)
                    # and connect it to a polydatamapper
                    mapper = vtkPolyDataMapper()
                    mapper.SetInput(cur_pipe['vtkPlaneSource'].GetOutput())
                    cur_pipe['vtkActor'].SetMapper(mapper)
                    cur_pipe['vtkActor'].SetTexture(cur_pipe['vtkTexture'])
                    self.renderers[i + 1].AddActor(cur_pipe['vtkActor'])
		    
		    self.setup_plane(cur_pipe)
		    if len(self.ortho_pipes[i]) == 1:
			self.setup_camera(cur_pipe, self.renderers[i+1])

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
	
	for layer_pl in self.ortho_pipes[r_idx - 1]:
	    reslice = layer_pl['vtkImageReslice']
	    o_extent = reslice.GetOutputExtent()
	    o_origin = reslice.GetOutputOrigin()
	    o_spacing = reslice.GetOutputSpacing()

	    reslice.SetOutputExtentToDefault()
	    reslice.SetOutputOriginToDefault()
	    reslice.SetOutputSpacingToDefault()
	    output = reslice.GetOutput()
	    output.UpdateInformation()
	    lo,hi = output.GetWholeExtent()[4:6]
	    s = output.GetSpacing()[2]
	    o = output.GetOrigin()[2]
	    lo = o + lo*s
	    hi = o + hi*s
	    orig_lo = min((lo,hi))
	    orig_hi = max((lo,hi))

	    print o_origin
	    delta = y - self.rw_lastxys[r_idx]['y']
	    o_origin = list(o_origin)
	    o_origin[2] = o_origin[2]+delta*o_spacing[2]
	    if (o_origin[2] > orig_hi):
		o_origin[2] = orig_hi
	    elif (o_origin[2] < orig_lo):
		o_origin[2] = orig_lo
	    o_origin = tuple(o_origin)

        reslice.SetOutputSpacing(o_spacing)
        reslice.SetOutputOrigin(o_origin)
        reslice.SetOutputExtent(o_extent)
	    
	    
	# at the end
	self.rw_lastxys[r_idx] = {'x' : x, 'y' : y}
	rw.Render()
    
	
