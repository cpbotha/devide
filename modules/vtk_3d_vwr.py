from module_base import module_base
import vtk
from wxPython.wx import *
from vtk.wx import wxVTKRenderWindow

class vtk_3d_vwr(module_base):
    def __init__(self, module_manager):
        module_base.__init__(self, module_manager)
	self.num_inputs = 5
	# list of dictionaries containing some input info
	# don't you just love Python List Comprehension?
	self.inputs = [{'Connected' : 0, 'vtkActor' : None}
                       for i in range(self.num_inputs)]

	# class variables we'll use alter
	self._renderer = None
	self._rw = None
	self._rw_frame = None
	
	# start up that gui
	self.create_window()
	
    def close(self):
	# remove all our references; close is used by __del__ or when
	# somebody wishes to destroy us
	for i in range(self.num_inputs):
	    # neatly remove all actors
	    self.set_input(i, None)
	if hasattr(self, '_renderer'):
	    del self._renderer
	if hasattr(self, '_rw'):
	    del self._rw
	if hasattr(self, '_rw_frame'):
	    self._rw_frame.Destroy()
	    del self._rw_frame
	    
    def create_window(self):
        parent_frame = self._module_manager.get_module_view_parent_window()
        self._rw_frame = wxFrame(parent=parent_frame, id=-1,
                                 title='3d viewer')
        EVT_CLOSE(self._rw_frame, lambda e, s=self: s._rw_frame.Show(false))

        self._rw = wxVTKRenderWindow.wxVTKRenderWindow(self._rw_frame, -1)
	
	self._renderer = vtk.vtkRenderer()
	self._rw.GetRenderWindow().AddRenderer(self._renderer)
	
    def get_input_descriptions(self):
	return self.num_inputs * ('vtkPolyData|vtkActor',)
	
    def set_input(self, idx, input_stream):
	if input_stream == None:
	    # now we should try to disconnect the input at idx
	    # (remove from renderer, del any bindings)
	    self.inputs[idx]['Connected'] = 0
	    if self.inputs[idx]['vtkActor'] != None:
		# take this actor out of the renderer
		self._renderer.RemoveActor(self.inputs[idx]['vtkActor'])
		# whether we've created or not, we have to remove our
                # reference (easy, huh?)
		self.inputs[idx]['vtkActor'] = None
	    
	# *sniff* this is so beautiful
	elif hasattr(input_stream, 'GetClassName') and \
             callable(input_stream.GetClassName):
	    # if we got this far, let's disconnect the input which is
            # connected at the moment
	    self.set_input(idx, None)
	    # and then continue with our game
	    if input_stream.GetClassName() == 'vtkPolyData':
		mapper = vtk.vtkPolyDataMapper()
		mapper.SetInput(input_stream)
		self.inputs[idx]['vtkActor'] = vtk.vtkActor()
		self.inputs[idx]['vtkActor'].SetMapper(mapper)
		self._renderer.AddActor(self.inputs[idx]['vtkActor'])
		self.inputs[idx]['Connected'] = 1
	    else:
		raise TypeError, "Wrong input type!"
		
    def get_output_descriptions(self):
	# return empty tuple
	return ()
	
    def get_output(self, idx):
	raise Exception

    def view(self):
        self._rw_frame.Show(true)
	
	

