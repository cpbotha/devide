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
	return (type(self.reader.GetOutput()),)

    # BASE
    def get_output(self, idx):
	return self.reader.GetOutput()
    
    def configure(self):
	# also show some intance name for this, or index into the module list
	config_window = Tix.Toplevel()
	
	
	# do we need a parent for this?
	pipeline_browser_window = Tix.Toplevel()
	# we don't have access to a renderer right now
	pipeline_browser = vtkPipelineSegmentBrowser(pipeline_browser_window, self.reader)
	pipeline_browser.pack (side='top', expand = 1, fill = 'both' )
