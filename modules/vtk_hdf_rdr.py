from module_base import module_base
import vtkpython
import vtkcpbothapython
from vtkPipeline.vtkPipeline import vtkPipelineBrowser, vtkPipelineSegmentBrowser
import Tkinter
import tkFileDialog
import Pmw

class vtk_hdf_rdr(module_base):
    def __init__(self):
	print "instantiating vtkHDFVolumeReader()"
	self.reader = vtkcpbothapython.vtkHDFVolumeReader()
	print "creating stringvar"
	self.filename = Tkinter.StringVar()
	print "syncing config"
	self.sync_config()
    
    def __del__(self):
	self.close()
	
    def close(self):
	if hasattr(self, 'reader'):
	    del self.reader
	    
    def get_input_descriptions(self):
	return ()
    
    def set_input(self, idx, input_stream):
	raise Exception
    
    def get_output_descriptions(self):
	return (self.reader.GetOutput().GetClassName(),)

    def get_output(self, idx):
	return self.reader.GetOutput()

    def sync_config(self):
	self.filename.set(self.reader.get_hdf_filename())
	
    def apply_config(self):
	self.reader.set_hdf_filename(self.filename.get())
	
    def execute_module(self):
	self.reader.Update()

    def view(self, parent_window=None):
	# first make sure that our variable agree with the stuff that we're configuring
	self.sync_config()
	
	# also show some intance name for this, or index into the module list
	config_window = Tkinter.Toplevel(parent_window)
	config_window.title("vtk_hdf_rdr.py configuration")
	config_window.protocol ("WM_DELETE_WINDOW", config_window.destroy)
	
	# the file prefix entry box
	Tkinter.Label(config_window, text="Filename").grid(row=0)
	Tkinter.Entry(config_window, textvariable=self.filename).grid(row=0, column=1)

	# button box
	box1 = Pmw.ButtonBox(config_window)
	box1.add('vtkHDFVolumeReader', command=lambda self=self, pw=parent_window: self.configure_vtk_object(self.reader, pw))
	box1.add('Pipeline', command=lambda self=self, pw=parent_window, vtk_objs=(self.reader): self.browse_vtk_pipeline(vtk_objs, pw))
	box1.grid(row=1, column=0, columnspan=2, sticky=Tkinter.W + Tkinter.E)
	box1.alignbuttons()

	self.add_CSAEO_box(config_window, 2, 2)
    
