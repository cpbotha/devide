import vtkpython

class vtk_mc_flt:
    def __init__(self):
	#self.reader = vtkpython.vtkVolume16Reader()
	print "__init__()"
	
    def __del__(self):
	# do some cleanup
	print "vtk_mc_flt.__del__()"
	
    def close(self):
	print "close()"
	
    # BASE
    def get_input_types(self):
	return ('vtkStructuredPoints',)
    
    # BASE
    def get_output_types(self):
	return ('vtkPolyData',)

    # BASE
    def get_output(self, idx):
	return None
    
    # BASE
    def get_input(self, idx):
	return None
