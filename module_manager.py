# TODO: the module_manager should maintain an internal record of which
# modules have been connected together

import sys, os, fnmatch
import string
import genUtils
import modules

class module_manager:
    """This class in responsible for picking up new modules in the modules 
    directory and making them available to the rest of the program."""
    
    def __init__(self, dscas3_app):
	"""Initialise module manager by fishing .py dscas3 modules from
	all pertinent directories."""
	
        self._dscas3_app = dscas3_app
	self.modules = []

        appdir = self._dscas3_app.get_appdir()
        self._modules_dir = os.path.join(appdir, 'modules')
        self._userModules_dir = os.path.join(appdir, 'userModules')
        
	# make first scan of available modules
	self.scan_modules()

        self._current_module = None

    def close(self):
        """Iterates through each module and closes it.

        This is only called during dscas3 application shutdown.
        """
        for module in self.modules:
            try:
                self.delete_module(module)
            except:
                # we can't allow a module to stop us
                pass

    def scan_modules(self):
	"""(Re)Check the modules directory for *.py files and put them in
	the list self.module_files."""
        self.module_list = []

	user_files = os.listdir(self._userModules_dir)

	for i in user_files:
	    if fnmatch.fnmatch(i, "*.py") and not fnmatch.fnmatch(i, "_*"):
		self.module_list.append(os.path.splitext(i)[0])

        self.module_list += modules.module_list

    def get_app_dir(self):
        return self._dscas3_app.get_appdir()
	
    def get_module_list(self):
	return self.module_list
    
    def get_modules_dir(self):
	return self._modules_dir

    def get_modules_xml_res_dir(self):
        return os.path.join(self._modules_dir, 'resources/xml')
    
    def get_modules(self):
	return self.modules

    def get_module_view_parent_window(self):
        # this could change
        return self._dscas3_app.get_main_window()
    
    def create_module(self, name):
	try:
            # find out whether it's built-in or user
            mtypePrefix = ['userModules', 'modules']\
                          [bool(name in modules.module_list)]
            fullName = mtypePrefix + '.' + name
	    # import the correct module
	    exec('import ' + fullName)
	    # and do this reload call as well (it's only double work on the
            # very first import)
	    # (but we should probably check if name exists in our dictionary,
            # and only use reload then.)
	    exec('reload(' + fullName + ')')
            print "imported: " + str(id(sys.modules[fullName]))
	    # then instantiate the requested class
	    exec('self.modules.append(' + fullName + '.' + name + '(self))')

	except ImportError:
	    genUtils.logError("Unable to import module %s!" % name)
	    return None
	except Exception, e:
	    genUtils.logError("Unable to instantiate module %s: %s" \
                                % (name, str(e)))
	    return None
	# return the instance
	return self.modules[-1]

    def view_module(self, instance):
        print dir(modules)
        instance.view()
    
    def delete_module(self, instance):
        # first make sure current_module isn't bound to the instance
        if self._current_module == instance:
            self._current_module = None
        # interesting... here we simply take the module out... this means
        # that with VTK ref counted things other modules that were dependent
        # on this can probably still continue with life
        # ATM, the when you delete a module from the graph editor, it
        # carefully takes care of all dependents;
	instance.close()
	# take away the reference AND remove (neat huh?)
	del self.modules[self.modules.index(instance)]
	
    def connect_modules(self, output_module, output_idx,
                        input_module, input_idx):
        """Connect output_idx'th output of provider output_module to
        input_idx'th input of consumer input_module.
        """

	input_module.setInput(input_idx, output_module.getOutput(output_idx))
	
    def disconnect_modules(self, input_module, input_idx):
        """Disconnect a consumer module from its provider.

        This method will disconnect input_module from its provider by
        disconnecting the link between the provider and input_module at
        the input_idx'th input port of input_module.
        """

	input_module.setInput(input_idx, None)
    
    def vtk_progress_cb(self, process_object):
        """Default callback that can be used for VTK ProcessObject callbacks.

        In all VTK-using child classes, this method can be used if such a
        class wants to show its process graphically.  You'll have to use
        a lambda callback in order to pass the process_object along.  See
        vtk_plydta_rdr.py for a simple example.
        """

        vtk_progress = process_object.GetProgress() * 100.0
        progressText = process_object.GetClassName() + ': ' + \
                       process_object.GetProgressText()
        if vtk_progress >= 100.0:
            progressText += ' [DONE]'

        self.setProgress(vtk_progress, progressText)

    def vtk_poll_error(self):
        """This method should be called whenever VTK processing might have
        taken place, e.g. in the execute() method of a dscas3 module.

        update() will be called on the central vtk_log_window.  This will
        only show if the filesize of the vtk log file has changed since the
        last call.
        """
        self._dscas3_app.update_vtk_log_window()

    def set_current_module(self, module):
        self._current_module = module

    def get_current_module(self):
        return self._current_module

    def setProgress(self, progress, message):
        self._dscas3_app.setProgress(progress, message)

	
