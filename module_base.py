# $Id: module_base.py,v 1.9 2002/03/19 13:53:37 cpbotha Exp $
import vtkpython
from vtkPipeline.vtkPipeline import vtkPipelineBrowser, vtkPipelineSegmentBrowser
from vtkPipeline.ConfigVtkObj import ConfigVtkObj
import Tkinter
import Pmw

class module_base:
    """Base class for all modules.  Any module wishing to take part in the dscas3
    party will have to offer all of these methods."""
    
    def __init__(self):
	raise NotImplementedError
	
    def __del__(self):
	self.close()
	
    def close(self):
	"""Idempotent method for de-initialising module as far as possible.  We
	can't guarantee the calling of __del__, as Python does garbage collection
	and the object might destruct a while after we've removed all references
	to it.  We call close() AGAIN from __del__ for obvious reasons, so
	make sure that your override is idempotent."""
	raise NotImplementedError
	
    def get_input_descriptions(self):
	"""Returns tuple of input descriptions, mostly used by the graph editor
	to make a nice glyph for this module."""
	raise NotImplementedError
    
    def set_input(self, idx, input_stream):
	"""Attaches input_stream (which is e.g. the output of a previous module)
	to this module's input at position idx."""
	raise NotImplementedError
    
    def get_output_descriptions(self):
	"""Returns a tuple of output descriptions, mostly used by the graph editor
	to make a nice glyph for this module.  These are also clues to the
	user as to which glyphs can be connected."""
	raise NotImplementedError

    def get_output(self, idx):
	"""Get the n-th output.  This will be used for connecting this output to
	the input of another module."""
	raise NotImplementedError
    
    def sync_config(self):
	raise NotImplementedError
    
    def apply_config(self):
	raise NotImplementedError
    
    def execute_module(self):
	raise NotImplementedError
    
    def view(self):
	"""Pop up a dialog with all config possibilities, including optional use
	of the pipeline browser."""
	raise NotImplementedError
    
    def add_CSAEO_box(self, parent_window, grid_row, col_span):
	"""Adds button box with cancel, sync, apply, execute and ok buttons.  this
	is standard for many of the modules.  The methods sync_config(), apply_config()
	and execute_module() have to be defined."""
	box2 = Pmw.ButtonBox(parent_window)
	box2.add('Cancel', command=parent_window.destroy)
	# synch settings with underlying code
	box2.add('Sync', command=self.sync_config)
	# apply settings
	box2.add('Apply', command=self.apply_config)
	# apply and execute
	box2.add('Execute', command=lambda self=self: (self.apply_config(), self.execute_module()))
	# apply and close dialog
	box2.add('Ok', command=lambda self=self, parent_window=parent_window: (self.apply_config(), parent_window.destroy()))

	balloon = Pmw.Balloon(parent_window)
	balloon.bind(box2.button(0), balloonHelp='Close this dialogue without applying.')
	balloon.bind(box2.button(1), balloonHelp='Synchronise dialogue with configuration of underlying system.')
	balloon.bind(box2.button(2), balloonHelp='Modify configuration of underlying system as specified by this dialogue.')
	balloon.bind(box2.button(3), balloonHelp='Apply, then execute the module.')
	balloon.bind(box2.button(4), balloonHelp='Apply, then close the window.')
	
	box2.grid(row=grid_row, column=0, columnspan=col_span, sticky=Tkinter.W + Tkinter.E)
    
    def browse_vtk_pipeline(self, vtk_objects, parent_window=None):
	"""Helper function for all derived classes.  They can call this method from
	their configure methods to start a vtk pipeline browsers on their internal
	VTK objects."""
	pipeline_browser_window = Tkinter.Toplevel(parent_window)
	# we don't have access to a renderer right now
	pipeline_browser = vtkPipelineSegmentBrowser(pipeline_browser_window, vtk_objects)
	# pack it
	pipeline_browser.pack (side='top', expand = 1, fill = 'both' )
    
    def configure_vtk_object(self, vtk_object, parent_window=None):
	"""Helper method for all derived classes.  They can call this method from
	their view methods to start Prabhu's vtk object configurator on an internal
	vtk object."""
	# we don't have access to a renderwindow now
	conf = ConfigVtkObj(None)
	conf.set_update_method(vtk_object)
        conf.configure (parent_window, vtk_object)
