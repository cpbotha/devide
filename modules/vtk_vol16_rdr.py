from module_base import module_base
import vtkpython
from vtkPipeline.vtkPipeline import vtkPipelineBrowser, vtkPipelineSegmentBrowser
import Tkinter
import tkFileDialog
import Pmw

class vtk_vol16_rdr(module_base):
    def __init__(self):
	# initialise vtkVolume16Reader
	self.reader = vtkpython.vtkVolume16Reader()

	self.file_prefix = Tkinter.StringVar()
	self.data_byte_order = Tkinter.IntVar()
	self.image_range = Tkinter.StringVar()
	self.data_dimensions = Tkinter.StringVar()
	self.data_spacing = Tkinter.StringVar()

	self.sync_config()
	
    def __del__(self):
	# do some cleanup
	print "vtk_volume16_reader.__del__()"
	self.close()
	
    # disconnect all inputs and outputs
    def close(self):
	# first check if this is bound
	if hasattr(self, 'reader'):
	    # if it still is, remove the binding
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
	self.file_prefix.set(self.reader.GetFilePrefix())
	self.data_byte_order.set(self.reader.GetDataByteOrder())
	self.image_range.set(self.reader.GetImageRange())
	self.data_dimensions.set(self.reader.GetDataDimensions())
	self.data_spacing.set(self.reader.GetDataSpacing())
    
    def apply_config(self):
	self.reader.SetFilePrefix(self.file_prefix.get())
	self.reader.SetDataByteOrder(self.data_byte_order.get())
	eval("self.reader.SetImageRange(%s)" % (self.image_range.get()))
	eval("self.reader.SetDataDimensions(%s)" % (self.data_dimensions.get()))
	eval("self.reader.SetDataSpacing(%s)" % (self.data_spacing.get()))
	
    def execute_module(self):
	self.reader.Update()
    
    def view(self, parent_window=None):
	# first make sure that our variable agree with the stuff that we're configuring
	self.sync_config()
	
	# also show some intance name for this, or index into the module list
	config_window = Tkinter.Toplevel(parent_window)
	config_window.title("vtk_vol16_rdr.py configuration")
	config_window.protocol ("WM_DELETE_WINDOW", config_window.destroy)
	
	# the file prefix entry box
	Tkinter.Label(config_window, text="File Prefix").grid(row=0)
	Tkinter.Entry(config_window, textvariable=self.file_prefix).grid(row=0, column=1)

	# radios for endianness
	Tkinter.Label(config_window, text="Endianness").grid(row=1)
	temp_frame = Tkinter.Frame(config_window)
	temp_frame.grid(row=1, column=1)
	Tkinter.Radiobutton(temp_frame, text="Big", variable=self.data_byte_order, value=0).pack(side=Tkinter.LEFT)
	Tkinter.Radiobutton(temp_frame, text="Little", variable=self.data_byte_order, value=1).pack(side=Tkinter.LEFT)
	
	# entry box for image range
	Tkinter.Label(config_window, text="Image Range").grid(row=2, column=0)
	Tkinter.Entry(config_window, textvariable=self.image_range).grid(row=2, column=1)

	# entry box for data dimensions
	Tkinter.Label(config_window, text="Data Dimensions").grid(row=3, column=0)
	Tkinter.Entry(config_window, textvariable=self.data_dimensions).grid(row=3, column=1)
	
	# and finally for data spacing
	Tkinter.Label(config_window, text="Data Spacing"). grid(row=4, column=0)
	Tkinter.Entry(config_window, textvariable=self.data_spacing).grid(row=4, column=1)
	
	# button box
	box1 = Pmw.ButtonBox(config_window)
	box1.add('vtkVolume16Reader', command=lambda self=self, pw=parent_window: self.configure_vtk_object(self.reader, pw))
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
	
