from module_base import module_base
import vtkpython
import Tix
from vtkPipeline.vtkPipeline import vtkPipelineBrowser, vtkPipelineSegmentBrowser

class vtk_mc_flt(module_base):
    def __init__(self):
	self.mc = vtkpython.vtkMarchingCubes()
	
    def __del__(self):
	# do some cleanup
	print "vtk_mc_flt.__del__()"
	self.close()
	
    def close(self):
	print "close()"
	# check that self.mc isn't deleted yet
        if dir(self).count('mc'):
	    del self.mc
	
    def get_input_descriptions(self):
	return ('vtkStructuredPoints',)
    
    def set_input(self, input_stream, idx):
	self.mc.SetInput(input_stream)
    
    def get_output_descriptions(self):
	return (self.mc.GetOutput().GetClassName(),)

    def get_output(self, idx):
	return self.mc.GetOutput()
    
    def configure(self, parent_window=None):
	# also show some intance name for this, or index into the module list
	config_window = Tix.Toplevel(parent_window)
	config_window.title("vtk_mc_flt.py configuration")
	config_window.protocol ("WM_DELETE_WINDOW", config_window.destroy)
	
	# button box
	box = Tix.ButtonBox(config_window, orientation=Tix.HORIZONTAL)
	box.add('pipeline', text='Pipeline', underline=0, width=6,
	command=lambda self=self, pw=parent_window, vtk_objs=(self.mc): self.browse_vtk_pipeline(vtk_objs, pw))
	box.pack(side=Tix.TOP, fill=Tix.X, expand=1)
