# $Id: module_base.py,v 1.14 2002/05/03 10:03:54 cpbotha Exp $

# ----------------------------------------------------------------------------

class module_base:
    """Base class for all modules.

    Any module wishing to take part in the dscas3 party will have to offer all
    of these methods.
    """
    
    def __init__(self, module_manager):
        """We need to know where the module manager is so we can query
        it about the module path, e.g.
        """
        self._module_manager = module_manager
	
    def close(self):
	"""Idempotent method for de-initialising module as far as possible.

        We can't guarantee the calling of __del__, as Python does garbage
        collection and the object might destruct a while after we've removed
        all references to it.

        In addition, with python garbage collection, __del__ can cause
        uncollectable objects, so try to avoid it as far as possible.
        """
	raise NotImplementedError

    def get_input_descriptions(self):
	"""Returns tuple of input descriptions, mostly used by the graph editor
	to make a nice glyph for this module."""
	raise NotImplementedError
    
    def set_input(self, idx, input_stream):
	"""Attaches input_stream (which is e.g. the output of a previous
        module) to this module's input at position idx.
        """
	raise NotImplementedError
    
    def get_output_descriptions(self):
	"""Returns a tuple of output descriptions.

        Mostly used by the graph editor to make a nice glyph for this module.
        These are also clues to the user as to which glyphs can be connected.
        """
	raise NotImplementedError

    def get_output(self, idx):
	"""Get the n-th output.

        This will be used for connecting this output to the input of another
        module.
        """
	raise NotImplementedError
    
    def sync_config(self):
	raise NotImplementedError
    
    def apply_config(self):
	raise NotImplementedError
    
    def execute_module(self):
	raise NotImplementedError
    
    def view(self):
	"""Pop up a dialog with all config possibilities, including optional
        use of the pipeline browser.
        """
	raise NotImplementedError
    
# ----------------------------------------------------------------------------

from vtkPipeline.ConfigVtkObj import ConfigVtkObj
from vtkPipeline.vtkPipeline import vtkPipelineBrowser

class module_mixin_vtk_pipeline_config:
    """Mixin to use for modules that want to make use of the vtkPipeline
    functionality.

    Modules that use this as mixin can make use of the vtk_object_configure
    and vtk_pipeline_configure methods to use ConfigVtkObj and
    vtkPipelineBrowser, respectively.  These methods will make sure that you
    use only one instance of a browser/config class per object.
    """

    def vtk_object_configure(self, parent, renwin, vtk_obj):
        """This will instantiate and show only one object config frame per
        unique vtk_obj (per module instance).

        If it is called multiple times for the same object, it will merely
        bring the pertinent window to the top (by show()ing).

        parent: parent wxWindow derivative.
        renwin: render window (optionally None) which will be
        render()ed when changes are made to the vtk object which is being
        configured.
        vtk_obj: the object you want to config.
        """ 
        if not hasattr(self, '_vtk_objs'):
            self._vtk_objs = {}
        if not self._vtk_objs.has_key(vtk_obj):
            self._vtk_objs[vtk_obj] = ConfigVtkObj(parent, renwin, vtk_obj)
        self._vtk_objs[vtk_obj].show()

    def vtk_pipeline_configure(self, parent, renwin, objects):
        """This will instantiate and show only one pipeline config per
        module instance.

        parent: parent wxWindow derivative.
        renwin: render window (optionally None) which will be render()ed
        when changes are made AND if objects is None, will be used to determine
        the pipeline.
        objects: if you don't want the pipeline to be extracted from the
        renderwindow, you can specify a sequence of objects to be used as the
        multiple roots of a partial pipeline.

        NOTE: renwin and objects can't BOTH be None/empty.
        """
        if not hasattr(self, '_pipeline') or self._pipeline == None:
            self._pipeline = vtkPipelineBrowser(parent, renwin, objects)
        self._pipeline.show()

            
