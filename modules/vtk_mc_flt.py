# vtk_mc_flt.py copyright (c) 2002 Charl P. Botha <cpbotha@ieee.org>
# $Id: vtk_mc_flt.py,v 1.14 2003/01/09 16:35:17 cpbotha Exp $
# vtk marching cubes filter

from gen_utils import log_error
from module_base import module_base, module_mixin_vtk_pipeline_config
import module_utils
import vtk
from wxPython.wx import *


class vtk_mc_flt(module_base):
    
    def __init__(self, module_manager):
        module_base.__init__(self, module_manager)
        
        # setup what we need of the VTK pipeline
	self.mc = vtkpython.vtkMarchingCubes()
        self.mc.SetProgressText('Performing Marching Cubes')
        self.mc.SetProgressMethod(lambda s=self, mm=mm::
                                  mm.vtk_progress_cb(s.mc))

        # setup our gui
        self._view_frame = None
        parent_window = self._module_manager.get_module_view_parent_window()
        self._create_view_frame(parent)


    #################################################################
    # module API methods
    #################################################################

    def apply_config(self):
        pass

    def close(self):
        # take care of that view_window
        self._view_frame.Destroy()
	# check that self.mc isn't deleted yet
        if hasattr(self, 'mc'):
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
        # self.isovalue.set(self.mc.GetValue(0))

    def view(self, parent_window=None):
        self.sync_config()
        self._view_frame.Show(true)        
        
    #################################################################
    # utility methods
    #################################################################
    
    def _create_view_frame(self, parent_window=None):
        """Create configuration/view window.

        This method sets up the config window and immediately hides it.  When
        the user wants to view/config, the window is simply de-iconised.
        """
        import resources.python.vtk_mc_flt_view
        reload(resources.python.vtk_mc_flt_view)
        
        self._view_frame = vtk_mc_flt_view.vtk_mc_flt_view_frame(parent_window)

        EVT_CLOSE(self._view_frame, lambda e, s=self: s._view_frame.Show(false))
        module_utils.bind_CSAEO2(self, self._view_frame)
