from module_base import module_base
import vtkpython
import Tix
from vtkPipeline.vtkPipeline import vtkPipelineBrowser, vtkPipelineSegmentBrowser

class vtk_vol16_rdr(module_base):
    def __init__(self):
	# initialise vtkVolume16Reader
	self.reader = vtkpython.vtkVolume16Reader()
	
    def __del__(self):
	# do some cleanup
	print "vtk_volume16_reader.__del__()"
	self.close()
	
    # disconnect all inputs and outputs
    def close(self):
	if dir(self).count('reader'):
	    del self.reader
	
    def get_input_descriptions(self):
	return ()
    
    def set_input(self, input_stream, idx):
	raise Exception
    
    def get_output_descriptions(self):
	return (self.reader.GetOutput().GetClassName(),)

    # BASE
    def get_output(self, idx):
	return self.reader.GetOutput()
    
    def configure(self, parent_window=None):
	# also show some intance name for this, or index into the module list
	config_window = Tix.Toplevel(parent_window)
	config_window.title("vtk_vol16_rdr.py configuration")
	config_window.protocol ("WM_DELETE_WINDOW", config_window.destroy)
	
	# button box
	box = Tix.ButtonBox(config_window, orientation=Tix.HORIZONTAL)
	box.add('pipeline', text='Pipeline', underline=0, width=6,
	command=lambda self=self, pw=parent_window, vtk_objs=(self.reader): self.browse_vtk_pipeline(vtk_objs, pw))
	box.pack(side=Tix.TOP, fill=Tix.X, expand=1)
	
