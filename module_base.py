# $Id: module_base.py,v 1.1 2002/02/15 14:45:41 cpbotha Exp $

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
	"""Returns list of input descriptions, mostly used by the graph editor
	to make a nice glyph for this module."""
	raise NotImplementedError
    
    def set_input(self, input_stream, idx):
	"""Attaches input_stream (which is e.g. the output of a previous module)
	to this module's input at position idx."""
	raise NotImplementedError
    
    def get_output_descriptions(self):
	"""Returns a list of output descriptions, mostly used by the graph editor
	to make a nice glyph for this module.  These are also clues to the
	user as to which glyphs can be connected."""
	raise NotImplementedError

    def get_output(self, idx):
	"""Get the n-th output.  This will be used for connecting this output to
	the input of another module."""
	raise NotImplementedError


