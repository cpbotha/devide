import sys, os, fnmatch
import copy
import genUtils
import modules
import mutex
from random import choice

class metaModule:
    """Class used to store module-related information.
    """
    
    def __init__(self, instance, instanceName):
        """Instance is the actual class instance and instanceName is a unique
        name that has been chosen by the user or automatically.
        """
        self.instance = instance        
        self.instanceName = instanceName
        self.resetInputsOutputs()

    def close(self):
        del self.instance
        del self.inputs
        del self.outputs

    def resetInputsOutputs(self):
        numIns = len(self.instance.getInputDescriptions())
        numOuts = len(self.instance.getOutputDescriptions())
        # numIns list of tuples of (supplierModule, supplierOutputIdx)
        self.inputs = [None] * numIns
        # numOuts list of lists of tuples of (consumerModule, consumerInputIdx)
        self.outputs = [[]] * numOuts

class pickledModuleState:
    def __init__(self):
        self.moduleConfig = None
        self.moduleName = None
        self.instanceName = None

class pickledConnection:
    def __init__(self, sourceInstanceName=None, outputIdx=None,
                 targetInstanceName=None, inputIdx=None, connectionType=None):
        
        self.sourceInstanceName = sourceInstanceName
        self.outputIdx = outputIdx
        self.targetInstanceName = targetInstanceName
        self.inputIdx = inputIdx
        self.connectionType = connectionType

class moduleManager:
    """This class in responsible for picking up new modules in the modules 
    directory and making them available to the rest of the program."""
    
    def __init__(self, dscas3_app):
	"""Initialise module manager by fishing .py dscas3 modules from
	all pertinent directories."""
	
        self._dscas3_app = dscas3_app
        # module dictionary, keyed on instance... cool.
        # values are metaModules
	self._moduleDict = {}

        appdir = self._dscas3_app.get_appdir()
        self._modules_dir = os.path.join(appdir, 'modules')
        self._userModules_dir = os.path.join(appdir, 'userModules')
        
	# make first scan of available modules
	self.scanModules()

        # this is a list of modules that have the ability to start a network
        # executing all by themselves and usually do... when we break down
        # a network, we should take these out first.  when we build a network
        # we should put them down last
        self.dangerousConsumerModules = ['slice3dVWR']

        # we'll use this to perform mutex-based locking on the progress
        # callback... (there SHOULD only be ONE moduleManager instance)
        self._inVTKProgressCallback = mutex.mutex()

    def close(self):
        """Iterates through each module and closes it.

        This is only called during dscas3 application shutdown.
        """

        # this is fine because .items() makes a copy of the dict
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

    def getInstanceName(self, instance):
        """Given the actual instance, return its unique instance.  If the
        instance doesn't exist in self._moduleDict, return the currently
        halfborn instance.
        """

        try:
            return self._moduleDict[instance].instanceName
        except Exception:
            return self._halfBornInstanceName

    def get_modules_dir(self):
	return self._modules_dir

    def get_module_view_parent_window(self):
        # this could change
        return self._dscas3_app.get_main_window()
    
    def createModule(self, name, instanceName=None):
	try:
            # think up name for this module (we have to think this up now
            # as the module might want to know about it whilst it's being
            # constructed
            instanceName = self._makeUniqueInstanceName(instanceName)
            self._halfBornInstanceName = instanceName
            
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
            moduleInstance = None
            exec('moduleInstance = %s.%s(self)' % (fullName, name))

            # and store it in our internal structures
            self._moduleDict[moduleInstance] = metaModule(moduleInstance,
                                                          instanceName)

            # it's now fully born ;)
            self._halfBornInstanceName = None


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

    def executeModule(self, instance):
        try:
            instance.executeModule()
        except Exception, e:
            mModule = self._moduleDict[instance]
            instanceName = mModule.instanceName
            moduleName = instance.__class__.__name__
            
            genUtils.logError('Unable to execute module %s (%s): %s' \
                              % (instanceName, moduleName, str(e)))

    def viewModule(self, instance):
        instance.view()
    
    def deleteModule(self, instance):
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

#         print "Deleted %s, %.2fM freed." % \
#               (instance.__class__.__name__,
#                (endFreeMemory - beginFreeMemory) / 1024.0 / 1024.0)
                                          
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
        # less consumer (if we even HAVE a supplier on this port)
        s = self._moduleDict[input_module].inputs[input_idx]
        if s:
            supp = s[0]
            suppOutIdx = s[1]
        
            oList = self._moduleDict[supp].outputs[suppOutIdx]
            del oList[oList.index((input_module, input_idx))]

        # indicate to the meta data that this module doesn't have an input
        # anymore
        self._moduleDict[input_module].inputs[input_idx] = None

    def deserialiseModuleInstances(self, pmsDict, connectionList):
        """Given a pickled stream, this method will recreate all modules,
        configure them and connect them up.  It returns a list of
        successfully instantiated modules.
        """
        
        # let's attempt to instantiate all the modules

        # newModulesDict will act as translator between pickled instanceName
        # and new instance!
        newModulesDict = {}
        for pmsTuple in pmsDict.items():
            # each pmsTuple == (instanceName, pms)
            newModule = self.createModule(pmsTuple[1].moduleName)
            if newModule:
                # set its config!
                try:
                    # we need to DEEP COPY the config, else it could easily
                    # happen that objects have bindings to the same configs!
                    # to see this go wrong, switch off the deepcopy, create
                    # a network by copying/pasting a vtkPolyData, load
                    # two datasets into a slice viewer... now save the whole
                    # thing and load it: note that the two readers are now
                    # reading the same file!
                    configCopy = copy.deepcopy(pmsTuple[1].moduleConfig)
                    print "DESERIALISE: %s" % \
                          (str(configCopy),)
                    newModule.setConfig(configCopy)
                except:
                    # it could be a module with no defined config logic
                    pass
                
                # and record that it's been recreated
                newModulesDict[pmsTuple[1].instanceName] = newModule

        # now we're going to connect all of the successfully created
        # modules together; first type 1 connections, then type 2 then type 3
        newConnections = []
        for connectionType in range(3):
            typeConnections = [connection for connection in connectionList
                               if connection.connectionType == connectionType]
            
            for connection in typeConnections:
                if newModulesDict.has_key(connection.sourceInstanceName) and \
                   newModulesDict.has_key(connection.targetInstanceName):
                    sourceM = newModulesDict[connection.sourceInstanceName]
                    targetM = newModulesDict[connection.targetInstanceName]
                    # attempt connecting them
                    print "connecting %s:%d to %s:%d..." % \
                          (sourceM.__class__.__name__, connection.outputIdx,
                           targetM.__class__.__name__, connection.inputIdx)

                    try:
                        self.connectModules(sourceM, connection.outputIdx,
                                            targetM, connection.inputIdx)
                    except:
                        pass
                    else:
                        newConnections.append(connection)

        # we return a dictionary, keyed on OLD pickled name with value
        # the newly created module-instance and a list with the connections
        return (newModulesDict, newConnections)

    def serialiseModuleInstances(self, moduleInstances):
        """Given 
        """

        # dictionary of pickled module instances keyed on unique module
        # instance name
        pmsDict = {}
        # we'll use this list internally to check later (during connection
        # pickling) which modules are being written away
        pickledModuleInstances = []
        
        for moduleInstance in moduleInstances:
            if self._moduleDict.has_key(moduleInstance):

                # first get the metaModule
                mModule = self._moduleDict[moduleInstance]
                
                # create a picklable thingy
                pms = pickledModuleState()
                
                try:
                    print "SERIALISE: %s - %s" % \
                          (str(moduleInstance),
                           str(moduleInstance.getConfig()))
                    pms.moduleConfig = moduleInstance.getConfig()
                except:
                    pms.moduleConfig = None
                    
                pms.moduleName = moduleInstance.__class__.__name__
                # this will only be used for uniqueness purposes
                pms.instanceName = mModule.instanceName

                pmsDict[pms.instanceName] = pms
                pickledModuleInstances.append(moduleInstance)

        # now iterate through all the actually pickled module instances
        # and store all connections in a connections list
        # three different types of connections:
        # 0. connections with source modules with no inputs
        # 1. normal connections
        # 2. connections with targets that are exceptions, e.g. sliceViewer
        connectionList = []
        for moduleInstance in pickledModuleInstances:
            mModule = self._moduleDict[moduleInstance]
            # we only have to iterate through all outputs
            for outputIdx in range(len(mModule.outputs)):
                outputConnections = mModule.outputs[outputIdx]
                # each output can of course have multiple outputConnections
                # each outputConnection is a tuple:
                # (consumerModule, consumerInputIdx)
                for outputConnection in outputConnections:
                    if outputConnection[0] in pickledModuleInstances:
                        # this means the consumerModule is also one of the
                        # modules to be pickled and so this connection
                        # should be stored

                        # find the type of connection (1, 2, 3), work from
                        # the back...
                        if outputConnection[0].__class__.__name__ in \
                           ['slice3dVWR']:
                            connectionType = 2
                        else:
                            connectionType = 1
                            # FIXME: we still have to check for 0: iterate
                            # through all inputs, check that none of the
                            # supplier modules are in the list that we're
                            # going to pickle
                            
                        
                        connection = pickledConnection(
                            mModule.instanceName, outputIdx,
                            self._moduleDict[outputConnection[0]].instanceName,
                            outputConnection[1],
                            connectionType)
                                                       
                        connectionList.append(connection)

        return (pmsDict, connectionList)
    
    def vtk_progress_cb(self, process_object):
        """Default callback that can be used for VTK ProcessObject callbacks.

        In all VTK-using child classes, this method can be used if such a
        class wants to show its process graphically.  You'll have to use
        a lambda callback in order to pass the process_object along.  See
        vtk_plydta_rdr.py for a simple example.
        """

        # if this is called while still in progress, we do nothing...
        # it means multi-threaded VTK objects are calling back into us (yuck)
        if self._inVTKProgressCallback.testandset():
            vtk_progress = process_object.GetProgress() * 100.0
            progressText = process_object.GetClassName() + ': ' + \
                           process_object.GetProgressText()
            if vtk_progress >= 100.0:
                progressText += ' [DONE]'

            self.setProgress(vtk_progress, progressText)
            self._inVTKProgressCallback.unlock()
            
    def vtk_poll_error(self):
        """This method should be called whenever VTK processing might have
        taken place, e.g. in the execute() method of a dscas3 module.

        update() will be called on the central vtk_log_window.  This will
        only show if the filesize of the vtk log file has changed since the
        last call.
        """
        self._dscas3_app.update_vtk_log_window()

    def setProgress(self, progress, message):
        """Progress is in percent.
        """
        self._dscas3_app.setProgress(progress, message)

    def _makeUniqueInstanceName(self, instanceName=None):
        """Ensure that instanceName is unique or create a new unique
        instanceName.

        If instanceName is None, a unique one will be created.  An
        instanceName (whether created or passed) will be permuted until it
        unique and then returned.
        """
        
        # first we make sure we have a unique instance name
        if not instanceName:
            instanceName = "d3m%d" % (len(self._moduleDict),)

        # now make sure that instanceName is unique
        uniqueName = False
        while not uniqueName:
            # first check that this doesn't exist in the module dictionary
            uniqueName = True
            for mmt in self._moduleDict.items():
                if mmt[1].instanceName == instanceName:
                    uniqueName = False
                    break

            if not uniqueName:
                # this means that this exists already!
                # create a random 3 character string
                chars = 'abcdefghijklmnopqrstuvwxyz'

                tl = ""
                for i in range(3):
                    tl += choice(chars)
                        
                instanceName = "%s%s%d" % (instanceName, tl,
                                           len(self._moduleDict))

        
        return instanceName
