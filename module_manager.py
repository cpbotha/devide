import sys, os, fnmatch
import Tix
import tkMessageBox
import traceback
import string

class module_manager:
    """This class in responsible for picking up new modules in the modules 
    directory and making them available to the rest of the program."""
    def __init__(self):
	"""Initialise module manager by fishing .py dscas3 modules from
	all pertinent directories."""
	
	self.modules = []
	
	# find out the module directory
	dirname = os.path.dirname(sys.argv[0])
	if dirname and dirname != os.curdir:
	    self.modules_dir = dirname + "/modules"
	else:
	    self.modules_dir = os.getcwd() + "/modules"
	    
	# add it to the python path so imports work
	sys.path.insert(0, self.modules_dir)
	# make first scan of available modules
	self.module_list = self.scan_modules()

    def scan_modules(self):
	"""(Re)Check the modules directory for *.py files and put them in
	the list self.module_files."""
	files = os.listdir(self.modules_dir)
	self.module_files = []
	for i in files:
	    if fnmatch.fnmatch(i, "*.py"):
		self.module_files.append(os.path.splitext(i)[0])
	# DON'T DO THIS HERE! (why not? - bloat!)
	# exec('import ' + self.module_files[-1])
	return self.module_files
	
    def get_module_list(self):
	return self.module_list
    
    def get_modules_dir(self):
	return self.modules_dir
    
    def get_modules(self):
	return self.modules
    
    def create_module(self, name):
	# it seems that objects instantiated in the try get destroyed in except(?)
	try:
	    # import the correct module
	    #exec('from ' + name + ' import ' + name)
	    exec('import ' + name)
	    # and do this reload call as well (it's only double work on the very first import)
	    # (but we should probably check if name exists in our dictionary, and only use reload
	    #  then.)
	    exec('reload(' + name + ')')
	    # then instantiate the requested class
	    exec('self.modules.append(' + name + '.' + name + '())')
	except ImportError:
	    tkMessageBox.showerror("Import error", "Unable to import module %s!" % name)
	    return None
	except Exception, e:
	    tkMessageBox.showerror("Instantiation error", "Unable to instantiate module %s: %s" % (name, str(e)))
            # add this traceback to some log window later
            # string.join( traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback), "\n" )            
            traceback.print_exc()
	    return None
	# return the instance
	return self.modules[-1]
    
    def delete_module(self, instance):
	instance.close()
	# take away the reference AND remove (neat huh?)
	del self.modules[self.modules.index(instance)]
	
    def connect_modules(self, output_module, output_idx, input_module, input_idx):
	input_module.set_input(input_idx, output_module.get_output(output_idx))
	
    def disconnect_modules(self, input_module, input_idx):
	print "disconnecting input %d of module %s" % (input_idx, input_module)
	input_module.set_input(input_idx, None)
    

	    
	

	
