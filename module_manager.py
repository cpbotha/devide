import sys, os, fnmatch

class module_manager:
    """This class in responsible for picking up new modules in the modules 
    directory and making them available to the rest of the program."""
    def __init__(self):
	"""Initialise module manager by fishing .py dscas3 modules from
	all pertinent directories."""
	
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

	    
	

	
