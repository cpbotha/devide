# $Id: moduleBase.py,v 1.13 2003/09/01 21:43:53 cpbotha Exp $

"""Module containing base class for dscas3 modules.

author: Charl P. Botha <cpbotha@ieee.org>
"""

class defaultConfigClass:
    pass

class moduleBase(object):
    """Base class for all modules.

    Any module wishing to take part in the dscas3 party will have to offer all
    of these methods.
    """
    
    def __init__(self, moduleManager):
        """Perform your module initialisation here.

        Please also call this init method
        (i.e. moduleBase.__init__(self)).  In your own __init__, you
        should create your view and show it to the user.

        """
        self._moduleManager = moduleManager

        
        self._config = defaultConfigClass()

    def close(self):
	"""Idempotent method for de-initialising module as far as possible.

        We can't guarantee the calling of __del__, as Python does garbage
        collection and the object might destruct a while after we've removed
        all references to it.

        In addition, with python garbage collection, __del__ can cause
        uncollectable objects, so try to avoid it as far as possible.
        """

        # we neatly get rid of some references
        del self._moduleManager

    def getInputDescriptions(self):
	"""Returns tuple of input descriptions, mostly used by the graph editor
	to make a nice glyph for this module."""
	raise NotImplementedError
    
    def setInput(self, idx, input_stream):
	"""Attaches input_stream (which is e.g. the output of a previous
        module) to this module's input at position idx.
        """
	raise NotImplementedError
    
    def getOutputDescriptions(self):
	"""Returns a tuple of output descriptions.

        Mostly used by the graph editor to make a nice glyph for this module.
        These are also clues to the user as to which glyphs can be connected.
        """
	raise NotImplementedError

    def getOutput(self, idx):
	"""Get the n-th output.

        This will be used for connecting this output to the input of another
        module.  Whatever is returned by this object MUST have an Update()
        method.  However you choose to implement it, the Update() should make
        sure that the whole chain of logic resulting in the data object has
        executed so that the data object is up to date.
        """
	raise NotImplementedError

    def logicToConfig(self):
        """Synchronise internal configuration information (usually
        self._config)with underlying system.
        """
        raise NotImplementedError

    def configToLogic(self):
        """Apply internal configuration information (usually self._config) to
        the underlying logic.
        """
        raise NotImplementedError

    def viewToConfig(self):
        """Synchronise internal configuration information with the view (GUI)
        of this module.

        """
        raise NotImplementedError
        
    
    def configToView(self):
        """Make the view reflect the internal configuration information.

        """
	raise NotImplementedError

    def applyViewToLogic(self):
        """Utility method that is used by the default CSAEO buttons.

        By default, applying changes to the underlying logic is followed
        by a synch of the view (via the config) to the underlying logic.
        The reason for this is to enable real-time display of other logic-
        dependent variables in the view.
        """
        
        self.viewToConfig()
        self.configToLogic()
        # this brings everything up to the surface again
        self.syncViewWithLogic()

    def syncViewWithLogic(self):
        """Utility method that is used by the default CSAEO buttons.
        """
        self.logicToConfig()
        self.configToView()
        
    def executeModule(self):
        """This should make the model do whatever processing it was designed
        to do.

        It's important that when this method is called, the module should be
        able to cause ALL of the modules preceding it in a glyph chain to
        execute (if necessary).  If the whole chain consists of VTK objects,
        this is easy.

        If not, extra measures need to be taken.  According to API,
        each output/input data object MUST have an Update() method
        that can ensure that the logic responsible for that object has
        executed thus making the data object current.

        In short, execute_module() should call Update() on all of this modules
        input objects, directly or indirectly.
        """
	raise NotImplementedError
    
    def view(self):
	"""Pop up a dialog with all config possibilities, including optional
        use of the pipeline browser.

        If the dialog is already visible, do something to draw the user's
        attention to it.  For a wxFrame-based view, you can do something like:
        if not frame.Show(True):
            frame.Raise()
        If the frame is already visible, this will bring it to the front.
        """
	raise NotImplementedError

    def getConfig(self):
        """Returns current configuration of module.

        This should return a pickle()able object that encapsulates all
        configuration information of this module.  The default just returns
        self._config, which is None by default.  You can override get_config()
        and set_config(), or just make sure that your config info always goes
        via self._config
        """
        return self._config

    def setConfig(self, aConfig):
        """Change configuration of module to that stored in aConfig.

        If set_config is called with the object previously returned by
        get_config(), the module should be in exactly the same state as it was
        when get_config() was called.  The default sets the default
        self._config and applies it to the underlying logic.
        """
        
        self._config = aConfig
        # apply the config to the underlying logic
        self.configToLogic()
        # bring it back all the way up to the view
        self.logicToConfig()
        self.configToView()

        
