# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

"""Module containing base class for devide modules.

author: Charl P. Botha <cpbotha@ieee.org>
"""

#########################################################################
class GenericObject(object):
    """Generic object into which we can stuff whichever attributes we want.
    """
    pass

#########################################################################
class DefaultConfigClass(object):
    pass

#########################################################################
class ModuleBase(object):
    """Base class for all modules.

    Any module wishing to take part in the devide party will have to offer all
    of these methods.
    """
    
    def __init__(self, module_manager):
        """Perform your module initialisation here.

        Please also call this init method
        (i.e. ModuleBase.__init__(self)).  In your own __init__, you
        should create your view and show it to the user.

        """
        self._module_manager = module_manager

        
        self._config = DefaultConfigClass()

        # modules should toggle this variable to True once they have
        # initialised and shown their view once.
        self.view_initialised = False

    def close(self):
        """Idempotent method for de-initialising module as far as possible.

        We can't guarantee the calling of __del__, as Python does garbage
        collection and the object might destruct a while after we've removed
        all references to it.

        In addition, with python garbage collection, __del__ can cause
        uncollectable objects, so try to avoid it as far as possible.
        """

        # we neatly get rid of some references
        del self._module_manager

    def get_input_descriptions(self):
        """Returns tuple of input descriptions, mostly used by the graph editor
        to make a nice glyph for this module."""
        raise NotImplementedError
        
    def set_input(self, idx, input_stream):
        """Attaches input_stream (which is e.g. the output of a previous
        module) to this module's input at position idx.

        If the previous value was None and the current value is not None, it
        signifies a connect and the module should initialise as if it's
        getting a new input.  This usually happens during the first network
        execution AFTER a connection.

        If the previous value was not-None and the new value is None, it
        signifies a disconnect and the module should take the necessary
        actions.  This usually happens immediatly when the user disconnects an
        input
        
        If the previous value was not-None and the current value is not-None,
        the module should take actions as for a changed input.  This event
        signifies a re-transfer on an already existing connection.  This can
        be considered an event for which this module is an observer.
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
        module.  Whatever is returned by this object MUST have an Update()
        method.  However you choose to implement it, the Update() should make
        sure that the whole chain of logic resulting in the data object has
        executed so that the data object is up to date.
        """
	raise NotImplementedError

    def logic_to_config(self):
        """Synchronise internal configuration information (usually
        self._config)with underlying system.

        You only need to implement this if you make use of the standard ECASH
        controls.
        """
        raise NotImplementedError

    def config_to_logic(self):
        """Apply internal configuration information (usually self._config) to
        the underlying logic.

        If this has resulted in changes to the logic, return True, otherwise
        return False

        You only need to implement this if you make use of the standard ECASH
        controls.
        """
        
        raise NotImplementedError

    def view_to_config(self):
        """Synchronise internal configuration information with the view (GUI)
        of this module.

        If this has resulted in changes to the config, return True,
        otherwise return False.

        You only need to implement this if you make use of the standard ECASH
        controls.
        """
        raise NotImplementedError
        
    
    def config_to_view(self):
        """Make the view reflect the internal configuration information.

        You only need to implement this if you make use of the standard ECASH
        controls.
        """
        raise NotImplementedError

    def execute_module(self):
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

    def get_config(self):
        """Returns current configuration of module.

        This should return a pickle()able object that encapsulates all
        configuration information of this module.  The default just returns
        self._config, which is None by default.  You can override get_config()
        and set_config(), or just make sure that your config info always goes
        via self._config

        In general, you should never need to override this.
        """

        # make sure that the config reflects the state of the underlying logic
        self.logic_to_config()
        # and then return the config struct.
        return self._config

    def set_config(self, aConfig):
        """Change configuration of module to that stored in aConfig.

        If set_config is called with the object previously returned by
        get_config(), the module should be in exactly the same state as it was
        when get_config() was called.  The default sets the default
        self._config and applies it to the underlying logic.

        In general, you should never need to override this.
        """
        
        self._config = aConfig
        # apply the config to the underlying logic
        self.config_to_logic()
        # bring it back all the way up to the view
        self.logic_to_config()

        # but only if we are in view mode
        if self.view_initialised:
            self.config_to_view()

        # the config has been set, so we assumem that the module has
        # now been modified. 
        self._module_manager.modify_module(self)

    # convenience functions

    def sync_module_logic_with_config(self):
        self._module_manager.sync_module_logic_with_config(self)

    def sync_module_view_with_config(self):
        self._module_manager.sync_module_view_with_config(self)

    def sync_module_view_with_logic(self):
        self._module_manager.sync_module_view_with_logic(self)


