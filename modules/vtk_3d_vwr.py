from module_base import module_base
import vtkpython
import Tix
from vtkPipeline.vtkPipeline import vtkPipelineBrowser, vtkPipelineSegmentBrowser

class vtk_3d_vwr(module_base):
    def __init__(self):
	self.rw_window = Tix.Toplevel(None)
	self.rw_window.title("3d viewer")
	# widthdraw hides the window, deiconify makes it appear again
	self.rw_window.protocol("WM_DELETE_WINDOW", self.rw_window.withdraw)
	
    def __del__(self):
	self.close()
	
    def close(self):
	if hasattr(self, 'rw_window'):
	    del self.rw_window
	    
    
