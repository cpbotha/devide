class vtk_vol16_rdr:
    def __init__(self):
	# initialise vtkVolume16Reader
	self.reader = vtkVolume16Reader()
	
    def __del__(self):
	print "vtk_volume16_reader.__del__()"

    def get_output(self):
	return self.reader.GetOutput()
    
