from module_base import module_base
import vtkpython
import Tix
from vtkPipeline.vtkPipeline import vtkPipelineBrowser, vtkPipelineSegmentBrowser

class vtk_vol16_rdr(module_base):
    def __init__(self):
	# initialise vtkVolume16Reader
	self.reader = vtkpython.vtkVolume16Reader()

	self.file_prefix = Tix.StringVar()
	self.data_byte_order = Tix.IntVar()
	self.image_range = Tix.StringVar()
	self.data_dimensions = Tix.StringVar()
	self.data_spacing = Tix.StringVar()
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
	config_window = Tix.Toplevel(parent_window)
	config_window.title("vtk_vol16_rdr.py configuration")
	config_window.protocol ("WM_DELETE_WINDOW", config_window.destroy)
	
	# the file prefix entry box
	Tix.Label(config_window, text="File Prefix").grid(row=0)
	Tix.Entry(config_window, textvariable=self.file_prefix).grid(row=0, column=1)

	# radios for endianness
	Tix.Label(config_window, text="Endianness").grid(row=1)
	temp_frame = Tix.Frame(config_window)
	temp_frame.grid(row=1, column=1)
	Tix.Radiobutton(temp_frame, text="Big", variable=self.data_byte_order, value=0).pack(side=Tix.LEFT)
	Tix.Radiobutton(temp_frame, text="Little", variable=self.data_byte_order, value=1).pack(side=Tix.LEFT)
	
	# entry box for image range
	Tix.Label(config_window, text="Image Range").grid(row=2, column=0)
	Tix.Entry(config_window, textvariable=self.image_range).grid(row=2, column=1)

	# entry box for data dimensions
	Tix.Label(config_window, text="Data Dimensions").grid(row=3, column=0)
	Tix.Entry(config_window, textvariable=self.data_dimensions).grid(row=3, column=1)
	
	# and finally for data spacing
	Tix.Label(config_window, text="Data Spacing"). grid(row=4, column=0)
	Tix.Entry(config_window, textvariable=self.data_spacing).grid(row=4, column=1)
	
	# button box
	box1 = Tix.ButtonBox(config_window, orientation=Tix.HORIZONTAL)
	box1.add('vtkvol16', text='vtkVolume16Reader', underline=0, command=lambda self=self, pw=parent_window: self.configure_vtk_object(self.reader, pw))
	box1.add('pipeline', text='Pipeline', underline=0, command=lambda self=self, pw=parent_window, vtk_objs=(self.reader): self.browse_vtk_pipeline(vtk_objs, pw))
	box1.grid(row=5, column=0, columnspan=2, sticky=Tix.W + Tix.E)

	box2 = Tix.ButtonBox(config_window, orientation=Tix.HORIZONTAL)
	box2.add('cancel', text='Cancel', underline=0, command=config_window.destroy)
	box2.add('sync', text='Sync', underline=0, command=self.sync_config)	
	box2.add('apply', text='Apply', underline=0, command=self.apply_config)
	box2.add('exec', text='Execute', underline=0, command=self.execute_module)
	box2.add('ok', text='Ok', underline=0, command=lambda self=self, config_window=config_window: self.apply_config() and config_window.destroy())
	box2.grid(row=6, column=0, columnspan=2, sticky=Tix.W + Tix.E)
	
