from module_base import module_base
from vtkpython import *
import Tkinter
import Pmw
from vtkPipeline.vtkPipeline import vtkPipelineBrowser, vtkPipelineSegmentBrowser

class vtk_plydta_rdr(module_base):

    def __init__(self):
	self.reader = vtkPolyDataReader()
	self.filename = Tkinter.StringVar()
	
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
	self.filename.set(self.reader.GetFileName())
	
    def apply_config(self):
	self.reader.SetFileName(self.filename.get())

    def execute_module(self):
	self.reader.Update()

    def view(self, parent_window=None):
	# first make sure that our variable agree with the stuff that we're configuring
	self.sync_config()
	
	# also show some intance name for this, or index into the module list
	config_window = Tkinter.Toplevel(parent_window)
	config_window.title("vtk_plydta_rdr.py configuration")
	config_window.protocol ("WM_DELETE_WINDOW", config_window.destroy)
	
	# the file prefix entry box
	Tkinter.Label(config_window, text="File Name").grid(row=0)
	Tkinter.Entry(config_window, textvariable=self.filename).grid(row=0, column=1)
	

	# button box
	box1 = Pmw.ButtonBox(config_window)
	box1.add('vtkPolyDataReader', command=lambda self=self, pw=parent_window: self.configure_vtk_object(self.reader, pw))
	box1.add('Pipeline', command=lambda self=self, pw=parent_window, vtk_objs=(self.reader): self.browse_vtk_pipeline(vtk_objs, pw))
	box1.grid(row=5, column=0, columnspan=2, sticky=Tkinter.W + Tkinter.E)
	box1.alignbuttons()

	box2 = Pmw.ButtonBox(config_window)
	box2.add('Cancel', command=config_window.destroy)
	# synch settings with underlying code
	box2.add('Sync', command=self.sync_config)
	# apply settings
	box2.add('Apply', command=self.apply_config)
	# apply and execute
	box2.add('Execute', command=lambda self=self: (self.apply_config(), self.execute_module()))
	# apply and close dialog
	box2.add('Ok', command=lambda self=self, config_window=config_window: (self.apply_config(), config_window.destroy()))

	balloon = Pmw.Balloon(config_window)
	balloon.bind(box2.button(0), balloonHelp='Close this dialogue without applying.')
	balloon.bind(box2.button(1), balloonHelp='Synchronise dialogue with configuration of underlying system.')
	balloon.bind(box2.button(2), balloonHelp='Modify configuration of underlying system as specified by this dialogue.')
	balloon.bind(box2.button(3), balloonHelp='Apply, then execute the module.')
	balloon.bind(box2.button(4), balloonHelp='Apply, then close the window.')
	
	box2.grid(row=6, column=0, columnspan=2, sticky=Tkinter.W + Tkinter.E)
	
