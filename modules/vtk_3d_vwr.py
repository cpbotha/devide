from module_base import module_base
from vtkpython import *
import Tkinter
from vtkPipeline.vtkPipeline import vtkPipelineBrowser, vtkPipelineSegmentBrowser
from vtkTkRenderWidget import vtkTkRenderWidget

class vtk_3d_vwr(module_base):
    def __init__(self):
	self.num_inputs = 5
	# list of dictionaries containing some input info
	# don't you just love Python List Comprehension?
	self.inputs = [{'Connected' : 0, 'vtkActor' : None} for i in range(self.num_inputs)]

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
	for i in range(self.num_inputs):
	    # neatly remove all actors
	    self.set_input(i, None)
	if hasattr(self, 'renderer'):
	    del self.renderer
	if hasattr(self, 'rw'):
	    del self.rw
	if hasattr(self, 'rw_window'):
	    self.rw_window.destroy()
	    del self.rw_window
	    
    def create_window(self):
    	self.rw_window = Tkinter.Toplevel(None)
	self.rw_window.title("3d viewer")
	# widthdraw hides the window, deiconify makes it appear again
	self.rw_window.protocol("WM_DELETE_WINDOW", self.rw_window.withdraw)
	
	self.rw = vtkTkRenderWidget(self.rw_window)
	self.renderer = vtkRenderer()
	self.rw.GetRenderWindow().AddRenderer(self.renderer)
	
       	self.rw.pack(side=Tkinter.TOP, fill=Tkinter.BOTH, expand=1)

    def get_input_descriptions(self):
	return self.num_inputs * ('vtkPolyData|vtkActor',)
	
    def set_input(self, idx, input_stream):
	if input_stream == None:
	    # now we should try to disconnect the input at idx
	    # (remove from renderer, del any bindings)
	    self.inputs[idx]['Connected'] = 0
	    if self.inputs[idx]['vtkActor'] != None:
		# take this actor out of the renderer
		self.renderer.RemoveActor(self.inputs[idx]['vtkActor'])
		# whether we've created or not, we have to remove our reference (easy, huh?)
		self.inputs[idx]['vtkActor'] = None
	    
	# *sniff* this is so beautiful
	elif hasattr(input_stream, 'GetClassName') and callable(input_stream.GetClassName):
	    # if we got this far, let's disconnect the input which is connected atm
	    self.set_input(idx, None)
	    # and then continue with our game
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
	
	

