# $Id: vtk_slice_vwr.py,v 1.2 2002/03/19 16:18:27 cpbotha Exp $

class vtk_slice_vwr(module_base):
    def __init__(self):
	self.rw_window = None
	self.rws = []
	self.renderers = []
	
	self.create_window()
	
    def __del__(self):
	print "__del__"
	
    def close(self):
	print "close"
	
    def create_window(self):
	self.rw_window = Tkinter.Toplevel(None)
	self.rw_window.title("slice viewer")
	# widthdraw hides the window, deiconify makes it appear again
	self.rw_window.protocol("WM_DELETE_WINDOW", self.rw_window.withdraw)
	

	for i in range(4):
	    self.rws.append(vtkTkRenderWidget(self.rw_window))
	    self.renderers.append(vtkRenderer())
	    # add last appended renderer to last appended vtkTkRenderWidget
	    self.rws[-1].GetRenderWindow().AddRenderer(self.renderers[-1])
	
	self.rws[0].grid(row=0, column=0, columnspan=3, sticky=Tkinter.W + Tkinter.E)
	self.rws[1].grid(row=1, column=0, sticky=Tkinter.W + Tkinter.E)
	self.rws[2].grid(row=1, column=1, sticky=Tkinter.W + Tkinter.E)
	self.rws[3].grid(row=1, column=2, sticky=Tkinter.W + Tkinter.E)
	
	
	
    
	
