import sys, os, fnmatch
import string
import gen_utils

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
        
	# add it to the python path so imports work
	sys.path.insert(0, self._modules_dir)
	# make first scan of available modules
	self.module_list = self.scan_modules()

    def scan_modules(self):
	"""(Re)Check the modules directory for *.py files and put them in
	the list self.module_files."""
	files = os.listdir(self._modules_dir)
	self.module_files = []
	for i in files:
	    if fnmatch.fnmatch(i, "*.py") and not fnmatch.fnmatch(i, "_*"):
		self.module_files.append(os.path.splitext(i)[0])
	# DON'T DO THIS HERE! (why not? - bloat!)
	# exec('import ' + self.module_files[-1])
	return self.module_files
	
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
	    # import the correct module
	    #exec('from ' + name + ' import ' + name)
	    exec('import ' + name)
	    # and do this reload call as well (it's only double work on the
            # very first import)
	    # (but we should probably check if name exists in our dictionary,
            # and only use reload then.)
	    exec('reload(' + name + ')')
	    # then instantiate the requested class
	    exec('self.modules.append(' + name + '.' + name + '(self))')
	except ImportError:
	    gen_utils.log_error("Unable to import module %s!" % name)
	    return None
	except Exception, e:
	    gen_utils.log_error("Unable to instantiate module %s: %s" \
                                % (name, str(e)))
	    return None
	# return the instance
	return self.modules[-1]

    def view_module(self, instance):
        instance.view()
    
    def delete_module(self, instance):
        # interesting... here we simply take the module out... this means
        # that with VTK ref counted things other modules that were dependent
        # on this can probably still continue with life
        # ATM, the when you delete a module from the graph editor, it
        # carefully takes care of all dependents;
	instance.close()
	# take away the reference AND remove (neat huh?)
	del self.modules[self.modules.index(instance)]
	
    def connect_modules(self, output_module, output_idx, input_module, input_idx):
	input_module.set_input(input_idx, output_module.get_output(output_idx))
	
    def disconnect_modules(self, input_module, input_idx):
	print "disconnecting input %d of module %s" % (input_idx, input_module)
	input_module.set_input(input_idx, None)
    
    def vtk_progress_cb(self, process_object):
        """Default callback that can be used for VTK ProcessObject callbacks.

        In all VTK-using child classes, this method can be used if such a
        class wants to show its process graphically.
        """

        vtk_progress = process_object.GetProgress() * 100.0
        self._dscas3_app.set_progress(vtk_progress,
                                      process_object.GetProgressText())

    def vtk_poll_error(self):
        """This method should be called whenever VTK processing might have
        taken place, e.g. in the execute() method of a dscas3 module.

        update() will be called on the central vtk_log_window.  This will
        only show if the filesize of the vtk log file has changed since the
        last call.
        """
        self._dscas3_app.update_vtk_log_window()

	

	
