# $Id: module_base.py,v 1.13 2002/04/27 00:51:56 cpbotha Exp $

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
    
