from module_base import module_base
import module_utils
import vtkpython
import Tkinter
from Tkconstants import *
import Pmw

class vtk_vol16_rdr(module_base):
    def __init__(self):
	# initialise vtkVolume16Reader
	self.reader = vtkpython.vtkVolume16Reader()

	self.file_prefix = Tkinter.StringVar()
	self.data_byte_order = Tkinter.StringVar()
	self.image_range = Tkinter.StringVar()
	self.data_dimensions = Tkinter.StringVar()
	self.data_spacing = Tkinter.StringVar()

	self.sync_config()
        self.config_window = None
        self.create_view_window()
	
    def __del__(self):
	# do some cleanup
	self.close()
	
    # disconnect all inputs and outputs
    def close(self):
        self.config_window.destroy()
	# first check if this is bound
	if hasattr(self, 'reader'):
	    # if it still is, remove the binding
	    del self.reader

    def create_view_window(self, parent_window=None):
	# also show some intance name for this, or index into the module list
	self.config_window = Tkinter.Toplevel(parent_window)
	self.config_window.title("vtk_vol16_rdr.py configuration")
	self.config_window.protocol ("WM_DELETE_WINDOW",
                                     self.config_window.withdraw)
        self.config_window.withdraw()

	efb_frame = Tkinter.Frame(self.config_window)
        efb_frame.pack(side=TOP, fill=X, expand=1, padx=5, pady=5)
        
	# the file prefix entry box
        fp_ef = Pmw.EntryField(efb_frame,
                               labelpos = 'w',
                               label_text = 'File prefix:',
                               validate = None,
                               entry_textvariable = self.file_prefix)
        fp_ef.pack(side=LEFT, fill=X, expand=1)

        browse_button = Tkinter.Button(efb_frame, text="Browse",
                                       command=lambda mu=module_utils, s=self:
                                       mu.fileopen_stringvar([("All files", "*.*")], s.file_prefix))
        browse_button.pack(side=LEFT)

        # radios for endianness
        e_rs = Pmw.RadioSelect(self.config_window,
                               buttontype = 'radiobutton',
                               orient = 'horizontal',
                               labelpos = 'w',
                               label_text = 'Endianness',
                               hull_borderwidth = 2,
                               hull_relief = 'ridge'
        )
        e_rs.pack(side=TOP, fill=X, expand = 1, padx = 5, pady = 5)
        e_rs.add('BigEndian', variable=self.data_byte_order)
        e_rs.add('LittleEndian', variable=self.data_byte_order)
	
	# entry box for image range
        ir_ef = Pmw.EntryField(self.config_window,
                               labelpos = 'w',
                               label_text = 'Image Range:',
                               validate = None,
                               entry_textvariable = self.image_range)
        ir_ef.pack(side=TOP, fill=X, expand=1, padx=5, pady=5)

	# entry box for data dimensions
        dd_ef = Pmw.EntryField(self.config_window,
                               labelpos = 'w',
                               label_text = 'Data Dimensions:',
                               validate = None,
                               entry_textvariable = self.data_dimensions)
        dd_ef.pack(side=TOP, fill=X, expand=1, padx=5, pady=5)

	# entry box for data spacing
        ds_ef = Pmw.EntryField(self.config_window,
                               labelpos = 'w',
                               label_text = 'Data Spacing:',
                               validate = None,
                               entry_textvariable = self.data_spacing)
        ds_ef.pack(side=TOP, fill=X, expand=1, padx=5, pady=5)

        # stuff all the label-entry elements in a tuple
        entries = (fp_ef, e_rs, ir_ef, dd_ef, ds_ef)
        # get Pmw to align them all nicely, no gridding required!
        Pmw.alignlabels(entries)
        
	# button box
	box1 = Pmw.ButtonBox(self.config_window)
	box1.add('vtkVolume16Reader', command=lambda self=self,
                 mu=module_utils, pw=parent_window:
                 mu.configure_vtk_object(self.reader, pw))
	box1.add('Pipeline', command=lambda self=self, pw=parent_window,
                 mu=module_utils, vtk_objs=(self.reader):
                 mu.browse_vtk_pipeline(vtk_objs, pw))
	box1.pack(side=TOP, fill=X, expand=1)
	box1.alignbuttons()

	module_utils.CSAEO_box(self, self.config_window).pack(side=TOP, fill=X,
                                                              expand=1)
        

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
	self.data_byte_order.set(self.reader.GetDataByteOrderAsString())
	self.image_range.set(self.reader.GetImageRange())
	self.data_dimensions.set(self.reader.GetDataDimensions())
	self.data_spacing.set(self.reader.GetDataSpacing())
    
    def apply_config(self):
	self.reader.SetFilePrefix(self.file_prefix.get())
        if self.data_byte_order.get() == "LittleEndian":
            self.reader.SetDataByteOrderToLittleEndian()
        else:
            self.reader.SetDataByteOrderToBigEndian()
	eval("self.reader.SetImageRange(%s)" % (self.image_range.get()))
	eval("self.reader.SetDataDimensions(%s)" % (self.data_dimensions.get()))
	eval("self.reader.SetDataSpacing(%s)" % (self.data_spacing.get()))
	
    def execute_module(self):
	self.reader.Update()
    
    def view(self, parent_window=None):
	# first make sure that our variable agree with the stuff that we're
        # configuring
	self.sync_config()
        # then pop up the config/view window
        self.config_window.deiconify()
        
	
