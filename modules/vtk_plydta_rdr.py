# $Id: vtk_plydta_rdr.py,v 1.3 2002/03/28 17:16:28 cpbotha Exp $

from module_base import module_base
from vtkpython import *
import Tkinter
from Tkconstants import *
import Pmw
import module_utils

class vtk_plydta_rdr(module_base):

    def __init__(self):
	self.reader = vtkPolyDataReader()
	self.filename = Tkinter.StringVar()
	
	self.sync_config()
        self.config_window = None
        self.create_view_window()
	
    def __del__(self):
	self.close()
	
    def close(self):
        self.config_window.destroy()
	if hasattr(self, 'reader'):
	    del self.reader

    def create_view_window(self, parent_window=None):
	# also show some intance name for this, or index into the module list
	self.config_window = Tkinter.Toplevel(parent_window)
	self.config_window.title("vtk_plydta_rdr.py configuration")
	self.config_window.protocol ("WM_DELETE_WINDOW",
                                     self.config_window.withdraw)
        self.config_window.withdraw()
	

        # make frame for entry and button
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
                                       mu.fileopen_stringvar([("VTK polydata files", "*.vtk"),("All files", "*.*")], s.filename))
        browse_button.pack(side=LEFT)

	# button box
	box1 = Pmw.ButtonBox(self.config_window)
	box1.add('vtkPolyDataReader', command=lambda self=self,
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
	self.filename.set(self.reader.GetFileName())
	
    def apply_config(self):
	self.reader.SetFileName(self.filename.get())

    def execute_module(self):
	self.reader.Update()

    def view(self, parent_window=None):
        self.sync_config()
        self.config_window.deiconify()
        
	
