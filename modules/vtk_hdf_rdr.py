# $Id: vtk_hdf_rdr.py,v 1.3 2002/03/27 16:35:56 cpbotha Exp $

from module_base import module_base
import vtkpython
import vtkcpbothapython
from vtkPipeline.vtkPipeline import vtkPipelineBrowser, \
     vtkPipelineSegmentBrowser
import Tkinter
import tkFileDialog
import Pmw

class vtk_hdf_rdr(module_base):
    """dscas3 module for reading dscas HDF datasets.

    The platform makes use of HDF SDS with a custom spacing attribute.
    """
    
    def __init__(self):
	print "instantiating vtkHDFVolumeReader()"
	self.reader = vtkcpbothapython.vtkHDFVolumeReader()
	print "creating stringvar"
	self.filename = Tkinter.StringVar()
	print "syncing config"
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
	
	# the file prefix entry box
	Tkinter.Label(self.config_window, text="Filename").grid(row=0)
	Tkinter.Entry(self.config_window, textvariable=self.filename).\
                                          grid(row=0, column=1)

	# button box
	box1 = Pmw.ButtonBox(self.config_window)
	box1.add('vtkHDFVolumeReader', command=lambda self=self,
                 pw=parent_window: self.configure_vtk_object(self.reader, pw))
	box1.add('Pipeline',
                 command=lambda self=self, pw=parent_window,
                 vtk_objs=(self.reader):
                 self.browse_vtk_pipeline(vtk_objs, pw))
	box1.grid(row=1, column=0, columnspan=2, sticky=Tkinter.W + Tkinter.E)
	box1.alignbuttons()

	self.add_CSAEO_box(self.config_window, 2, 2)
        
        

    def view(self, parent_window=None):
	# first make sure that our variables agree with the stuff that
        # we're configuring
	self.sync_config()
        self.config_window.deiconify()
        
	
    
