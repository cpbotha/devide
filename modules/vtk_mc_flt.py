# vtk_mc_flt.py copyright (c) 2002 Charl P. Botha <cpbotha@ieee.org>
# $Id: vtk_mc_flt.py,v 1.13 2003/01/08 16:16:57 cpbotha Exp $
# vtk marching cubes filter

from gen_utils import log_error
from module_base import module_base, module_mixin_vtk_pipeline_config
import module_utils
import vtk
from wxPython.wx import *
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor

class vtk_mc_flt(module_base):
    
    def __init__(self, module_manager):
        module_base.__init__(self, module_manager)
        
        # setup what we need of the VTK pipeline
	self.mc = vtkpython.vtkMarchingCubes()
        self.mc.SetProgressText('Performing Marching Cubes')
        self.mc.SetProgressMethod(lambda s=self, mm=mm::
                                  mm.vtk_progress_cb(s.mc))

        # setup our gui
        self._create_view_frame()

    #################################################################
    # module API methods
    #################################################################

    def apply_config(self):
        pass

    def close(self):
        # take care of that view_window
        self._view_frame.Destroy()
	# check that self.mc isn't deleted yet
        del self.mc

    def execute_module(self):
        self.mc.Update()
        self._module_manager.vtk_poll_error()

    def get_input_descriptions(self):
	return ('Volume data (vtkImageData)',)
        
    def get_output(self, idx):
	return self.mc.GetOutput()

    def get_output_descriptions(self):
	return ('Extracted surfaces (vtkPolyData)',)

    def set_input(self, idx, input_stream):
	self.mc.SetInput(input_stream)

    def sync_config(self):
        # for now we act as if we have one isovalue
        self.isovalue.set(self.mc.GetValue(0))

    def view(self, parent_window=None):
        self.sync_config()
        self.config_window.deiconify()
        
    #################################################################
    # utility methods
    #################################################################
    
    def create_view_window(self, parent_window=None):
        """Create configuration/view window.

        This method sets up the config window and immediately hides it.  When
        the user wants to view/config, the window is simply de-iconised.
        """
	self.config_window = Tkinter.Toplevel(parent_window)
	self.config_window.title("vtk_mc_flt.py configuration")
	self.config_window.protocol ("WM_DELETE_WINDOW",
                                     self.config_window.withdraw)


        iso_entry = Pmw.EntryField(self.config_window,
                                   labelpos = 'w',
                                   value = '55.5',
                                   label_text = 'Isovalue:',
                                   validate = {'validator' : 'real'},
                                   entry_textvariable=self.isovalue)
        iso_entry.grid(row=0,column=0)
        #iso_entry.pack(side=TOP)
        
	
	# button box
	box = Pmw.ButtonBox(self.config_window)
	box.add('vtkMarchingCubes', command=lambda self=self,
                pw=parent_window: self.configure_vtk_object(self.mc, pw))
	box.add('pipeline', text='Pipeline', command=lambda self=self,
                pw=parent_window, vtk_objs=(self.mc):
                self.browse_vtk_pipeline(vtk_objs, pw))
	box.grid(row=1, column=0, columnspan=1, sticky=W+E)
        #box.pack(side=TOP)
        box.alignbuttons()

        self.add_CSAEO_box(self.config_window, 2, 1)
        
        self.config_window.withdraw()

	
    


