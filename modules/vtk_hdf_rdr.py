# $Id: vtk_hdf_rdr.py,v 1.5 2002/03/28 16:02:18 cpbotha Exp $

from module_base import module_base
import vtkpython
import vtkcpbothapython
import Tkinter
from Tkconstants import *
import Pmw
import module_utils

class vtk_hdf_rdr(module_base):
    """dscas3 module for reading dscas HDF datasets.

    The platform makes use of HDF SDS with a custom spacing attribute.
    """
    
    def __init__(self):
	self.reader = vtkcpbothapython.vtkHDFVolumeReader()
	self.filename = Tkinter.StringVar()
	self.sync_config()
        # declare this var here out of good habit
        self.config_window = None
        # go on, create that view window
        self.create_view_window()
    
    def __del__(self):
	self.close()
	
    def close(self):
        self.config_window.destroy()
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

    def create_view_window(self, parent_window=None):
        """Create configuration/view window.

        This method sets up the config window and immediately hides it.  When
        the user wants to view/config, the window is simply de-iconised.
        """
        
	# also show some intance name for this, or index into the module list
	self.config_window = Tkinter.Toplevel(parent_window)
	self.config_window.title("vtk_hdf_rdr.py configuration")
	self.config_window.protocol ("WM_DELETE_WINDOW",
                                self.config_window.withdraw)
        self.config_window.withdraw()

	efb_frame = Tkinter.Frame(self.config_window)
        efb_frame.pack(side=TOP, fill=X, expand=1, padx=5, pady=5)
        
	# the file prefix entry box
        Pmw.EntryField(efb_frame,
                       labelpos = 'w',
                       label_text = 'Filename:',
                       validate = None,
                       entry_textvariable = self.filename).pack(side=LEFT,
                                                                fill=X,
                                                                expand=1)

        browse_button = Tkinter.Button(efb_frame, text="Browse",
                                       command=lambda mu=module_utils, s=self:
                                       mu.fileopen_stringvar([("HDF files", "*.hdf"),("All files", "*.*")], s.filename))
        browse_button.pack(side=LEFT)

	# button box
	box1 = Pmw.ButtonBox(self.config_window)
	box1.add('vtkHDFVolumeReader', command=lambda self=self,
                 mu=module_utils,
                 pw=parent_window: mu.configure_vtk_object(self.reader, pw))
	box1.add('Pipeline',
                 command=lambda self=self, pw=parent_window,
                 mu=module_utils, vtk_objs=(self.reader):
                 mu.browse_vtk_pipeline(vtk_objs, pw))
	box1.pack(side=TOP, fill=X, expand=1)
	box1.alignbuttons()

	module_utils.CSAEO_box(self, self.config_window).pack(side=TOP, fill=X,
                                                              expand=1)
        
    def view(self, parent_window=None):
	# first make sure that our variables agree with the stuff that
        # we're configuring
	self.sync_config()
        self.config_window.deiconify()
        
	
    
