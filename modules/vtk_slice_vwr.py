# $Id: vtk_slice_vwr.py,v 1.3 2002/03/20 23:01:49 cpbotha Exp $
from module_base import module_base
from vtkpython import *
import Tkinter
from Tkconstants import *
import Pmw
from vtkPipeline.vtkPipeline import vtkPipelineBrowser, vtkPipelineSegmentBrowser
from vtkTkRenderWidget import vtkTkRenderWidget


class vtk_slice_vwr(module_base):
    def __init__(self):
	self.num_inputs = 5
	self.rw_window = None
	self.rws = []
	self.renderers = []
	
	self.create_window()
	
    def __del__(self):
	self.close()
	
    def close(self):
	if hasattr(self, 'renderers'):
	    del self.renderers
	if hasattr(self, 'rws'):
	    del self.rws
	if hasattr(self,'rw_window'):
	    self.rw_window.destroy()
	    del self.rw_window
	
    def create_window(self):
	self.rw_window = Tkinter.Toplevel(None)
	self.rw_window.title("slice viewer")
	# widthdraw hides the window, deiconify makes it appear again
	self.rw_window.protocol("WM_DELETE_WINDOW", self.rw_window.withdraw)
	
	# paned widget with two panes, one for 3d window the other for ortho views
	# default vertical (i.e. divider is horizontal line)
	# hull width and height refer to the whole thing!
	rws_pane = Pmw.PanedWidget(self.rw_window, hull_width=600, hull_height=400)
	rws_pane.add('top3d', size=200)
        rws_pane.add('orthos', size=200)	

	# the 3d window
	self.rws.append(vtkTkRenderWidget(rws_pane.pane('top3d'), width=600, height=200))
	self.renderers.append(vtkRenderer())
	# add last appended renderer to last appended vtkTkRenderWidget
	self.rws[-1].GetRenderWindow().AddRenderer(self.renderers[-1])
	self.rws[-1].pack(side=TOP, fill=BOTH, expand=1) # 3d window is at the top
	
	# pane containing three ortho views
	ortho_pane = Pmw.PanedWidget(rws_pane.pane('orthos'), orient='horizontal', hull_width=600, hull_height=150)
	ortho_pane.pack(side=TOP, fill=BOTH, expand=1)
	
	ortho_pane.add('ortho0', size=200)
	ortho_pane.add('ortho1', size=200)
	ortho_pane.add('ortho2', size=200)	
	for i in range(3):
	    self.rws.append(vtkTkRenderWidget(ortho_pane.pane('ortho%d' % (i)), width=200, height=150))
	    self.renderers.append(vtkRenderer())
	    # add last appended renderer to last appended vtkTkRenderWidget
	    self.rws[-1].GetRenderWindow().AddRenderer(self.renderers[-1])
	    self.rws[-1].pack(side=LEFT, fill=BOTH, expand=1)

	rws_pane.pack(side=TOP, fill=BOTH, expand=1)

    def get_input_descriptions(self):
	# concatenate it num_inputs times (but these are shallow copies!)
	return self.num_inputs * ('vtkStructuredPoints|vtkImageData|vtkPolyData',)
    
    def set_input(self, idx, input_stream):
	print "set_input"
	
    def get_output_descriptions(self):
	# return empty tuple
	return ()
	
    def get_output(self, idx):
	raise Exception

    def view(self):
	self.rw_window.deiconify()
    
	
    
	
