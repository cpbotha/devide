from module_base import module_base
import vtkpython

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
	raise NotImplementedError
    
    def get_output_descriptions(self):
	return ('vtkPolyData',)

    def get_output(self, idx):
	return None
    
