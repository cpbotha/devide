import vtkpython

class vtk_vol16_rdr:
    def __init__(self):
	# initialise vtkVolume16Reader
	self.reader = vtkpython.vtkVolume16Reader()
	
    def __del__(self):
	# do some cleanup
	del self.reader
	print "vtk_volume16_reader.__del__()"
	
    # BASE
    def get_input_types(self):
	return ()
    
    # BASE
    def get_output_types(self):
	return (type(self.reader.GetOutput()),)

    # BASE
    def get_output(self, idx):
	return self.reader.GetOutput()
    
    # BASE
    def get_input(self, idx):
    
