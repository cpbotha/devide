from module_base import module_base
from vtkpython import *
import Tix
from vtkPipeline.vtkPipeline import vtkPipelineBrowser, vtkPipelineSegmentBrowser
from vtkTkRenderWidget import vtkTkRenderWidget

class vtk_3d_vwr(module_base):
    def __init__(self):
	# list of dictionaries containing some input info
	self.inputs = []	
	for i in range(5):
	    self.inputs.append({'Connected' : 0, 'vtkActor' : None})

	# class variables we'll use alter
	self.renderer = None
	self.rw = None
	self.rw_window = None
	
	# start up that gui
	self.create_window()
	
    def __del__(self):
	self.close()
	
    def close(self):
	# remove all our references; close is used by __del__ or when
	# somebody wishes to destroy us
	if hasattr(self, 'renderer'):
	    del self.renderer
	if hasattr(self, 'rw'):
	    del self.rw
	if hasattr(self, 'rw_window'):
	    self.rw_window.destroy()
	    del self.rw_window
	    
    def create_window(self):
    	self.rw_window = Tix.Toplevel(None)
	self.rw_window.title("3d viewer")
	# widthdraw hides the window, deiconify makes it appear again
	self.rw_window.protocol("WM_DELETE_WINDOW", self.rw_window.withdraw)
	
	self.rw = vtkTkRenderWidget(self.rw_window)
	self.renderer = vtkRenderer()
	self.rw.GetRenderWindow().AddRenderer(self.renderer)
	
	self.rw.pack(side=Tix.TOP)
	
	
    def get_input_descriptions(self):
	return ('vtkPolyData|vtkActor', 'vtkPolyData|vtkActor', 'vtkPolyData|vtkActor', 'vtkPolyData|vtkActor', 'vtkPolyData|vtkActor')
	
    def set_input(self, idx, input_stream):
	if input_stream == None:
	    # now we should try to disconnect the input at idx
	    # (remove from renderer, del any bindings)
	    print "eeke"
	    
	# *sniff* this is so beautiful
	elif hasattr(input_stream, 'GetClassName') and callable(input_stream.GetClassName):
	    if input_stream.GetClassName() == 'vtkPolyData':
		mapper = vtkPolyDataMapper()
		mapper.SetInput(input_stream)
		self.inputs[idx]['vtkActor'] = vtkActor()
		self.inputs[idx]['vtkActor'].SetMapper(mapper)
		self.renderer.AddActor(self.inputs[idx]['vtkActor'])
		self.inputs[idx]['Connected'] = 1
	    else:
		raise TypeError, "Wrong input type!"
		
    def get_output_descriptions(self):
	# return empty tuple
	return ()
	
    def get_output(self, idx):
	raise Exception

    def view(self):
	self.rw_window.deiconify()
	
	

