# TODO: the module_manager should maintain an internal record of which
# modules have been connected together

import sys, os, fnmatch
import string
import genUtils
import modules

class metaModule:
    def __init__(self, instance):
        self.instance = instance
        self.resetInputsOutputs()

    def close(self):
        del self.instance
        del self.inputs
        del self.outputs

    def resetInputsOutputs(self):
        numIns = len(self.instance.getInputDescriptions())
        numOuts = len(self.instance.getOutputDescriptions())
        # numIns list of tuples of (supplierModule, supplierOutputIdx)
        self.inputs = [None for i in range(numIns)]
        # numOuts list of lists of tuples of (consumerModule, consumerInputIdx)
        self.outputs = [[] for i in range(numOuts)]
        

class moduleManager:
    """This class in responsible for picking up new modules in the modules 
    directory and making them available to the rest of the program."""
    
    def __init__(self, dscas3_app):
	"""Initialise module manager by fishing .py dscas3 modules from
	all pertinent directories."""
	
        self._dscas3_app = dscas3_app
        # module dictionary, keyed on instance... cool.
	self._moduleDict = {}

        appdir = self._dscas3_app.get_appdir()
        self._modules_dir = os.path.join(appdir, 'modules')
        self._userModules_dir = os.path.join(appdir, 'userModules')
        
	# make first scan of available modules
	self.scanModules()

        self._current_module = None

    def close(self):
        """Iterates through each module and closes it.

        This is only called during dscas3 application shutdown.
        """

        # FIXME: rework this code!  you can't walk down the list and delete
        # each module, because delete actually removes the module from the
        # list!
        for mModule in self._moduleDict.items():
            try:
                self.deleteModule(mModule.instance)
            except:
                # we can't allow a module to stop us
                pass

    def scanModules(self):
	"""(Re)Check the modules directory for *.py files and put them in
	the list self.module_files."""
        self._availableModuleList = []

	user_files = os.listdir(self._userModules_dir)

	for i in user_files:
	    if fnmatch.fnmatch(i, "*.py") and not fnmatch.fnmatch(i, "_*"):
		self._availableModuleList.append(os.path.splitext(i)[0])

        self._availableModuleList += modules.module_list

    def get_app_dir(self):
        return self._dscas3_app.get_appdir()
	
    def getAvailableModuleList(self):
	return self._availableModuleList
    
    def get_modules_dir(self):
	return self._modules_dir

    def get_module_view_parent_window(self):
        # this could change
        return self._dscas3_app.get_main_window()
    
    def createModule(self, name):
	try:
            # find out whether it's built-in or user
            mtypePrefix = ['userModules', 'modules']\
                          [bool(name in modules.module_list)]
            fullName = mtypePrefix + '.' + name

            # perform the conditional import/reload
            self.importReload(fullName)
            # importReload requires this afterwards for safety reasons
            exec('import %s' % fullName)
            # in THIS case, there is a McMillan hook which'll tell the
            # installer about all the dscas3 modules. :)
                
            print "imported: " + str(id(sys.modules[fullName]))
	    # then instantiate the requested class
            exec('moduleInstance = %s.%s(self)' % (fullName, name))
	    #exec('self.modules.append(' + fullName + '.' + name + '(self))')
            numIns = len(moduleInstance.getInputDescriptions())
            numOuts = len(moduleInstance.getOutputDescriptions())
            self._moduleDict[moduleInstance] = metaModule(moduleInstance)

	except ImportError:
	    genUtils.logError("Unable to import module %s!" % name)
	    return None
	except Exception, e:
	    genUtils.logError("Unable to instantiate module %s: %s" \
                                % (name, str(e)))
	    return None
                                    
	# return the instance
	return moduleInstance

    def importReload(self, fullName):
        """This will import and reload a module if necessary.  Use this only
        for things in modules or userModules.

        If we're NOT running installed, this will run import on the module.
        If it's not the first time this module is imported, a reload will
        be run straight after.

        If we're running installed, reloading only makes sense for things in
        userModules, so it's only done for these modules.  At the moment,
        the stock Installer reload() is broken.  Even with my fixes, it doesn't
        recover memory used by old modules, see:
        http://trixie.triqs.com/pipermail/installer/2003-May/000303.html
        This is one of the reasons we try to avoid unnecessary reloads.

        You should use this as follows:
        moduleManager.importReloadModule('full.path.to.my.module')
        import full.path.to.my.module
        so that the module is actually brought into the calling namespace.

        importReload used to return the modulePrefix object, but this has
        been changed to force module writers to use a conventional import
        afterwards so that the McMillan installer will know about dependencies.
        """

        # this should yield modules or userModules
        modulePrefix = fullName.split('.')[0]

        # determine whether this is a new import
        if not sys.modules.has_key(fullName):
            newModule = True
        else:
            newModule = False
                
        # import the correct module - we have to do this in anycase to
        # get the thing into our local namespace
        exec('import ' + fullName)
            
        # there can only be a reload if this is not a newModule
        if not newModule:
            if not self.isInstalled() or \
                   modulePrefix == 'userModules':
                # we only reload if we're not running from an Installer
                # package (the __importsub__ check) OR if we are running
                # from Installer, but it's a userModule; there's no sense
                # in reloading a module from an Installer package as these
                # can never change in anycase
                exec('reload(' + fullName + ')')

        # we need to inject the import into the calling dictionary...
        # importing my.module results in "my" in the dictionary, so we
        # split at '.' and return the object bound to that name
        # return locals()[modulePrefix]
        # we DON'T do this anymore, so that module writers are forced to
        # use an import statement straight after calling importReload (or
        # somewhere else in the module)

    def isInstalled(self):
        """Returns True if dscas3 is running from an Installed state.
        Installed of course refers to being installed with Gordon McMillan's
        Installer.  This can be used by dscas3 modules to determine whether
        they should use reload or not.
        """
        return hasattr(modules, '__importsub__')

    def viewModule(self, instance):
        instance.view()
    
    def deleteModule(self, instance):
        # first make sure current_module isn't bound to the instance
        if self._current_module == instance:
            self._current_module = None

        # first disconnect all outgoing connections
        inputs = self._moduleDict[instance].inputs
        outputs = self._moduleDict[instance].outputs

        # outputs is a list of lists of tuples, each tuple containing
        # moduleInstance and inputIdx of the consumer module
        for output in outputs:
            if output:
                # we just want to walk through the dictionary tuples
                for consumer in output:
                    # disconnect all consumers
                    consumer[0].setInput(consumer[1], None)
                    # the setInput could fail, which would throw an exception,
                    # but that's really just too deep: just in case
                    # we set it to None
                    consumer[0] = None
                    consumer[1] = -1

        # inputs is a list of tuples, each tuple containing moduleInstance
        # and outputIdx of the producer/supplier module
        for inputIdx in range(len(inputs)):
            instance.setInput(inputIdx, None)
            # set supplier to None - so we know it's nuked
            inputs[inputIdx] = None

        # we've disconnected completely - let's reset all lists
        self._moduleDict[instance].resetInputsOutputs()

        # now we can finally call close on the instance
	instance.close()
        # if that worked (i.e. no exception) let's remove it from the dict
        del self._moduleDict[instance]
	
    def connectModules(self, output_module, output_idx,
                        input_module, input_idx):
        """Connect output_idx'th output of provider output_module to
        input_idx'th input of consumer input_module.
        """

	input_module.setInput(input_idx, output_module.getOutput(output_idx))
        
        # update the inputs thingy on the input_module
        self._moduleDict[input_module].inputs[input_idx] = (output_module,
                                                            output_idx)

        #
        self._moduleDict[output_module].outputs[output_idx].append(
            (input_module, input_idx))
	
    def disconnectModules(self, input_module, input_idx):
        """Disconnect a consumer module from its provider.

        This method will disconnect input_module from its provider by
        disconnecting the link between the provider and input_module at
        the input_idx'th input port of input_module.
        """

	input_module.setInput(input_idx, None)

        # trace it back to our supplier, and tell it that it has one
        # less consumer
        supp = self._moduleDict[input_module].inputs[input_idx][0]
        suppOutIdx = self._moduleDict[input_module].inputs[input_idx][1]
        
        oList = self._moduleDict[supp].outputs[suppOutIdx]
        del oList[oList.index((input_module, input_idx))]

        # indicate to the meta data that this module doesn't have an input
        # anymore
        self._moduleDict[input_module].inputs[input_idx] = None
        
    
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

	
