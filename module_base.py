# $Id: module_base.py,v 1.21 2002/09/30 15:30:30 cpbotha Exp $

# ----------------------------------------------------------------------------

"""Module containing class-related utilities and code for dscas3 modules.

In this module you'll find a base class as well as several useful mixins.
Please see the documentation.

author: Charl P. Botha <cpbotha@ieee.org>
"""

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
        module.  Whatever is returned by this object MUST have an Update()
        method.  However you choose to implement it, the Update() should make
        sure that the whole chain of logic resulting in the data object has
        executed so that the data object is up to date.
        """
	raise NotImplementedError
    
    def sync_config(self):
        """Synchronise module view with configuration of underlying system.
        """
	raise NotImplementedError
    
    def apply_config(self):
        """Apply changes that have been made to view (dialogue) to the
        underlying system.
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
        """
	raise NotImplementedError
    
# ----------------------------------------------------------------------------

from external.vtkPipeline.ConfigVtkObj import ConfigVtkObj
from external.vtkPipeline.vtkPipeline import vtkPipelineBrowser

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

        parent: parent wxWindow derivative.  It's important to pass a parent,
        else the here-created window might never be destroyed.
        renwin: render window (optionally None) which will be
        render()ed when changes are made to the vtk object which is being
        configured.
        vtk_obj: the object you want to config.
        """ 
        if not hasattr(self, '_vtk_obj_cfs'):
            self._vtk_obj_cfs = {}
        if not self._vtk_obj_cfs.has_key(vtk_obj):
            self._vtk_obj_cfs[vtk_obj] = ConfigVtkObj(parent, renwin, vtk_obj)
        self._vtk_obj_cfs[vtk_obj].show()

    def close_vtk_object_configure(self):
        """Explicitly close() all ConfigVtkObj's that vtk_objct_configure has
        created.

        Usually, the ConfigVtkObj windows will be children of some frame, and
        when that frame gets destroyed, they will be too.  However, when this
        is not the case, you can make use of this method.
        """
        if hasattr(self, '_vtk_obj_cfs'):
            for key in self._vtk_obj_cfs.keys():
                self._vtk_obj_cfs[key].close()
            self._vtk_obj_cfs.clear()

    def vtk_pipeline_configure(self, parent, renwin, objects=None):
        """This will instantiate and show only one pipeline config per
        specified renwin and objects.

        parent: parent wxWindow derivative.  It's important to pass a parent,
        else the here-created window might never be destroy()ed.
        renwin: render window (optionally None) which will be render()ed
        when changes are made AND if objects is None, will be used to determine
        the pipeline.
        objects: if you don't want the pipeline to be extracted from the
        renderwindow, you can specify a sequence of objects to be used as the
        multiple roots of a partial pipeline.

        NOTE: renwin and objects can't BOTH be None/empty.
        """
        if not hasattr(self, '_vtk_pipeline_cfs'):
            self._vtk_pipeline_cfs = {}
            
        # create a dictionary key: a tuple containing renwin + objects
        # (if objects != None)
        this_key = (renwin,)
        if objects:
            this_key = this_key + objects
            
        # see if we have this pipeline lying around or not
        # if not, create it and store
        if not self._vtk_pipeline_cfs.has_key(this_key):
            self._vtk_pipeline_cfs[this_key] = vtkPipelineBrowser(
                parent, renwin, objects)

        # yay display
        self._vtk_pipeline_cfs[this_key].show()

    def close_pipeline_configure(self):
        """Explicitly close() the pipeline browser of this module.

        This should happen automatically if a valid 'parent' was passed to
        vtk_pipeline_configure(), i.e. when the parent dies, the pipeline
        browser will die too.  However, you can use this method to take
        care of it explicitly.
        """
        if hasattr(self, '_vtk_pipeline_cfs'):
            for key in self._vtk_pipeline_cfs:
                self._vtk_pipeline_cfs[key].close()

        self._vtk_pipeline_cfs.clear()
        

            
# ----------------------------------------------------------------------------

from wxPython.wx import wxFileDialog, wxDirDialog, wxOPEN, wxID_OK

class module_mixin_fo_dialog:
    """Module mixin to make use of file open dialog."""
    
    def fn_browse(self, parent, message, wildcard, style=wxOPEN):
        """Utility method to make use of wxFileDialog.

        This function will open up exactly one dialog per 'message' and this
        dialog won't be destroyed.  This persistence makes sure that the dialog
        retains its previous settings and also that there is less overhead for
        subsequent creations.  The dialog will be a child of 'parent', so when
        parent is destroyed, this dialog will be too.
        """
        if not hasattr(self, '_fo_dlgs'):
            self._fo_dlgs = {}
        if not self._fo_dlgs.has_key(message):
            self._fo_dlgs[message] = wxFileDialog(parent,
                                                  message, "", "",
                                                  wildcard, style)
        if self._fo_dlgs[message].ShowModal() == wxID_OK:
            return self._fo_dlgs[message].GetPath()
        else:
            return None

    def close_fn_browse(self):
        """Use this method to close all created dialogs explicitly.

        This should be taken care of automatically if you've passed in a valid
        'parent'.  Use this method in cases where this was not possible.
        """
        if hasattr(self, '_fo_dlgs'):
            for key in self._fo_dlgs.keys():
                self._fo_dlgs[key].Destroy()
            self._fo_dlgs.clear()

    def dn_browse(self, parent, message, default_path=""):
        """Utility method to make use of wxDirDialog.

        This function will open up exactly one dialog per 'message' and this
        dialog won't be destroyed.  This function is more or less identical
        to fn_browse().
        """
        if not hasattr(self, '_do_dlgs'):
            self._do_dlgs = {}

        if not self._do_dlgs.has_key(message):
            self._do_dlgs[message] = wxDirDialog(parent, message, default_path)

        if self._do_dlgs[message].ShowModal() == wxID_OK:
            return self._do_dlgs[message].GetPath()
        else:
            return None

        
