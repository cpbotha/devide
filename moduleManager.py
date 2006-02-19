# moduleManager.py copyright (c) 2005 Charl P. Botha http://cpbotha.net/
# $Id$

import sys, os, fnmatch
import re
import copy
import genUtils
from metaModule import metaModule
import modules
import mutex
from random import choice
from moduleBase import defaultConfigClass
import time
import types

# some notes with regards to extra module state/logic required for scheduling
# * in general, executeModule()/transferOutput()/etc calls do exactly that
#   when called, i.e. they don't automatically cache.  The scheduler should
#   take care of caching by making the necessary isModified() or
#   shouldTransfer() callls.  The reason for this is so that the module
#   actions can be forced
#

# notes with regards to execute on change:
# * devide.py should register a "change" handler with the moduleManager.
#   I've indicated places with "execute on change" where I think this
#   handler should be invoked.  devide.py can then invoke the scheduler.

#########################################################################
class moduleManagerException(Exception):
    pass
    
#########################################################################

#########################################################################
class pickledModuleState:
    def __init__(self):
        self.moduleConfig = None
        # e.g. modules.Viewers.histogramSegment
        self.moduleName = None
        # this is the unique name of the module, e.g. dvm15
        self.instanceName = None

#########################################################################
class pickledConnection:
    def __init__(self, sourceInstanceName=None, outputIdx=None,
                 targetInstanceName=None, inputIdx=None, connectionType=None):
        
        self.sourceInstanceName = sourceInstanceName
        self.outputIdx = outputIdx
        self.targetInstanceName = targetInstanceName
        self.inputIdx = inputIdx
        self.connectionType = connectionType

#########################################################################
class moduleManager:
    """This class in responsible for picking up new modules in the modules 
    directory and making them available to the rest of the program.

    @todo: we should split this functionality into a moduleManager and
    networkManager class.  One moduleManager per processing node,
    global networkManager to coordinate everything.

    @todo: ideally, ALL module actions should go via the metaModule.
    
    @author: Charl P. Botha <http://cpbotha.net/>
    """
    
    def __init__(self, devide_app):
	"""Initialise module manager by fishing .py devide modules from
	all pertinent directories.
        """
	
        self._devide_app = devide_app
        # module dictionary, keyed on instance... cool.
        # values are metaModules
	self._moduleDict = {}

        # we use this to store temporary bindings to modules so that
        # they can be scripted with
        self._markedModules = {}

        appdir = self._devide_app.get_appdir()
        self._modules_dir = os.path.join(appdir, 'modules')
        #sys.path.insert(0,self._modules_dir)
        
        self._userModules_dir = os.path.join(appdir, 'userModules')

        ############################################################
        # initialise module Kits - Kits are collections of libraries
        # that modules can depend on.  The Kits also make it possible
        # for us to write hooks for when these libraries are imported
        import module_kits
        # remove no-kits from module_kit_list:
        nmkl = [mk for mk in module_kits.module_kit_list
                if mk not in self.getAppMainConfig().nokits]
        module_kits.module_kit_list = nmkl

        # now import the kits that remain
        for module_kit in module_kits.module_kit_list:
            # import module_kit into module_kits namespace
            exec('import module_kits.%s' % (module_kit,))
            # call module_kit.init()
            getattr(module_kits, module_kit).init(self)

        ##############################################################
        
	# make first scan of available modules
	self.scanModules()

        # auto_execute mode, still need to link this up with the GUI
        self.auto_execute = True

        # this is a list of modules that have the ability to start a network
        # executing all by themselves and usually do... when we break down
        # a network, we should take these out first.  when we build a network
        # we should put them down last

        # slice3dVWRs must be connected LAST, histogramSegment second to last
        # and all the rest before them
        self.consumerTypeTable = {'slice3dVWR' : 5,
                                  'histogramSegment' : 4}

        # we'll use this to perform mutex-based locking on the progress
        # callback... (there SHOULD only be ONE moduleManager instance)
        self._inProgressCallback = mutex.mutex()

        # array of no exception module execution errors
        self._noExcModuleExecError = []


    def close(self):
        """Iterates through each module and closes it.

        This is only called during devide application shutdown.
        """

        # this is fine because .items() makes a copy of the dict
        for mModule in self._moduleDict.values():
            try:
                self.deleteModule(mModule.instance)
            except:
                # we can't allow a module to stop us
                pass

    def addNoExcModuleExecError(self, message):
        """Method that can be called by module execute functions to indicate
        errors (as an alternative to throwing an exception).

        This method belongs to the per-processing node part of the module
        manager.
        """
        
        self._noExcModuleExecError.append(message)

    def applyModuleViewToLogic(self, instance):
        """Interface method that can be used by clients to transfer module
        view to underlying logic.

        This is usually called by moduleUtils and thunks through to the
        relevant metaModule call.
        """

        mModule = self._moduleDict[instance]
        mModule.applyViewToLogic()

        # execute on change

    def syncModuleViewWithLogic(self, instance):
        """Interface method that can be used by clients to transfer config
        information from the underlying module logic (model) to the view.
        """

        mModule = self._moduleDict[instance]
        mModule.syncModuleViewWithLogic()

    def scanModules(self):
	"""(Re)Check the modules directory for *.py files and put them in
	the list self.module_files.
        """

        self._availableModules = {}
        appDir = self._devide_app.get_appdir()
        modulePath = self.get_modules_dir()

        # search through modules hierarchy and pick up all module_index files
        ####################################################################

        moduleIndices = []

        def miwFunc(arg, dirname, fnames):
            moduleIndices.extend([os.path.join(dirname, fname)
                                  for fname in fnames
                                  if fnmatch.fnmatch(fname, 'module_index.py')])

        os.path.walk(modulePath, miwFunc, arg=None)

        # iterate through the moduleIndices, building up the available
        # modules list.
        import module_kits # we'll need this to check available kits
        failed_mis = {}
        for mi in moduleIndices:
            # mi is a full path
            # remove modulePath from the beginning and extension from the end
            mi2 = os.path.splitext(mi.replace(modulePath, ''))[0]
            # replace path separator with .
            mim = mi2.replace(os.path.sep, '.')

            # Class.mod style
            # and remove possible '.' at beginning
            #if mim.startswith('.'):
            #    mim = mim[1:]

            # modules.Class.mod style
            mim = 'modules%s' % (mim,)

            try:
                # now we can import
                __import__(mim, globals(), locals())
                
            except Exception, e:
                # make a list of all failed moduleIndices
                failed_mis[mim] = sys.exc_info()
                msgs = genUtils.exceptionToMsgs()

                # and log them as mesages
                self._devide_app.logMessage(
                    'Error loading %s: %s.' % (mi, str(e)))

                for m in msgs:
                    self._devide_app.logMessage(m.strip(), timeStamp=False)

                # we don't want to throw an exception here, as that would
                # mean that a singe misconfigured module_index file can
                # prevent the whole scanModules process from completing
                # so we'll report on errors here and at the end

            else:
                # reload, as this could be a run-time rescan
                m = sys.modules[mim]
                reload(m)
            
                # find all classes in the imported module
                cs = [a for a in dir(m)
                      if type(getattr(m,a)) == types.ClassType]

                # stuff these classes, keyed on the module name that they
                # represent, into the modules list.
                for a in cs:
                    # a is the name of the class
                    c = getattr(m,a)

                    module_deps = True
                    for kit in c.kits:
                        if kit not in module_kits.module_kit_list:
                            module_deps = False
                            break

                    if module_deps:
                        module_name = mim.replace('module_index', a)
                        self._availableModules[module_name] = c

        # we should move this functionality to the graphEditor.  "segments"
        # are _probably_ only valid there... alternatively, we should move
        # the concept here

        segmentList = []
        def swFunc(arg, dirname, fnames):
            segmentList.extend([os.path.join(dirname, fname)
                                for fname in fnames
                                if fnmatch.fnmatch(fname, '*.dvn')])

        os.path.walk(os.path.join(appDir, 'segments'), swFunc, arg=None)

#         segmentList = []
#         recursiveDirectoryD3MNSearch(os.path.join(appDir, 'segments'),
#                                      None, segmentList)

        self.availableSegmentsList = segmentList


        # report on accumulated errors - this is still a non-critical error
        # so we don't throw an exception.
        if len(failed_mis) > 0:
            failed_indices = '\n'.join(failed_mis.keys())
            self._devide_app.logError(
                ['The following module indices failed to load: \n%s' % \
                 (failed_indices,)])
        

    ########################################################################
    def old_scanmodules_code(self):
        def recursiveDirectoryD3MNSearch(adir, curModulePath, mnList):
            """Iterate recursively starting at adir and make a list of
            all available modules and networks.

            We do not traverse into dirs that are named 'resources' or that
            end with 'modules'.
            """

            if curModulePath:
                wildCard = "*.py"
            else:
                wildCard = "*.dvn"
                
            fileNames = os.listdir(adir)
            for fileName in fileNames:
                completeName = os.path.join(adir, fileName)
                if os.path.isdir(completeName) and \
                       fileName.strip('/') != 'resources' and \
                       not fileName.strip('/').lower().endswith('modules'):
                    # fileName is just a directory name then
                    # make sure it has no /'s at the end and append
                    # it to the curModulePath when recursing
                    newCurModulePath = None
                    if curModulePath:
                        newCurModulePath = curModulePath + '.' + \
                                           fileName.strip('/')

                    recursiveDirectoryD3MNSearch(
                        completeName,
                        newCurModulePath,
                        mnList)

                elif os.path.isfile(completeName) and \
                         fnmatch.fnmatch(fileName, wildCard) and \
                         not fnmatch.fnmatch(fileName, "_*"):
                    if curModulePath:
                        mnList.append(
                            "%s.%s" % (curModulePath,
                                       os.path.splitext(fileName)[0]))
                    else:
                        mnList.append(completeName)
        

        userModuleList = []
        recursiveDirectoryD3MNSearch(os.path.join(appDir,
                                                    'userModules'),
                                       'userModules', userModuleList)


        # make sure we pick it up if someone has edited the moduleList
        reload(modules)
        # first add the core modules to our central list
        for mn in modules.moduleList:
            self._availableModules['modules.%s' % (mn,)] = \
                                                   modules.moduleList[mn]


        
        # now do the modulePacks
        # first get a list of directories in modulePacks
        modulePacksDir = os.path.join(appDir, 'modulePacks')        
        try:
            mpdcands = os.listdir(modulePacksDir)
        except Exception, e:
            print "Could not list modulePacks: %s." % (str(e),)
        else:
            try:
                import modulePacks
            except ImportError, e:
                print "Could not import modulePacks: %s." % (str(e),)
            else:
                mpdirs = [mpdir for mpdir in mpdcands
                          if os.path.isdir(
                    os.path.join(modulePacksDir, mpdir))]

                for mpdir in mpdirs:
                    # this should remove trailing dirseps
                    mpdir = os.path.normpath(mpdir)
                    try:
                        # import the modulePack
                        __import__('modulePacks.%s' % (mpdir,),
                                   globals(), locals())
                        # reload it
                        reload(getattr(modulePacks, mpdir))
                    except ImportError:
                        # skip to next mpdir
                        continue

                    mpdirModuleList = getattr(modulePacks, mpdir).moduleList
                    for mn,cats in mpdirModuleList.items():
                        self._availableModules['modulePacks.%s.%s' %
                                                  (mpdir, mn)] = cats
                                                  

            

        # then all the user modules
        for umn in userModuleList:
            self._availableModules['%s' % (umn,)] = \
                                           ('userModules',)
        

    def get_app_dir(self):
        return self.getAppDir()

    def getAppDir(self):
        return self._devide_app.getAppDir()

    def getAppMainConfig(self):
        return self._devide_app.mainConfig
	
    def getAvailableModules(self):
        """Return the availableModules, a dictionary keyed on fully qualified
        module name (e.g. modules.Readers.vtiRDR) with values the classes
        defined in module_index files.
        """
        
	return self._availableModules


    def getInstance(self, instanceName):
        """Given the unique instance name, return the instance itself.
        If the module doesn't exist, return None.
        """

        found = False
        for instance, mModule in self._moduleDict.items():
            if mModule.instanceName == instanceName:
                found = True
                break

        if found:
            return mModule.instance

        else:
            return None

    def getInstanceName(self, instance):
        """Given the actual instance, return its unique instance.  If the
        instance doesn't exist in self._moduleDict, return the currently
        halfborn instance.
        """

        try:
            return self._moduleDict[instance].instanceName
        except Exception:
            return self._halfBornInstanceName

    def get_meta_module(self, instance):
        """Given an instance, return the corresponding meta_module.

        @param instance: the instance whose meta_module should be returned.
        @return: meta_module corresponding to instance.
        @raise KeyError: this instance doesn't exist in the moduleDict.
        """
        return self._moduleDict[instance]

    def get_modules_dir(self):
        return self._modules_dir

    def get_module_view_parent_window(self):
        # this could change
        return self.getModuleViewParentWindow()

    def getModuleViewParentWindow(self):
        """Get parent window for module windows.

        THIS METHOD WILL BE DEPRECATED.  The ModuleManager and view-less
        (back-end) modules shouldn't know ANYTHING about windows or UI
        aspects.
        """
        
        try:
            return self._devide_app.get_interface().get_main_window()
        except AttributeError:
            # the interface has no main_window
            return None
    
    def createModule(self, fullName, instanceName=None):
        """Try and create module fullName.

        If an error occurs, this will be directly logged with
        devideApp.logError.  Think about this: shouldn't this function rather
        raise an exception?

        @param fullName: The complete module spec below application directory,
        e.g. modules.Readers.hdfRDR.

        @return: moduleInstance if successful, None if not.
        """
        
	try:
            # think up name for this module (we have to think this up now
            # as the module might want to know about it whilst it's being
            # constructed
            instanceName = self._makeUniqueInstanceName(instanceName)
            self._halfBornInstanceName = instanceName
            
            # perform the conditional import/reload
            self.importReload(fullName)
            # importReload requires this afterwards for safety reasons
            exec('import %s' % fullName)
            # in THIS case, there is a McMillan hook which'll tell the
            # installer about all the devide modules. :)

    	    # then instantiate the requested class
            moduleInstance = None
            exec('moduleInstance = %s.%s(self)' % (fullName,
                                                   fullName.split('.')[-1]))

            if hasattr(moduleInstance, 'PARTS_TO_INPUTS'):
                pti = moduleInstance.PARTS_TO_INPUTS
            else:
                pti = None

            if hasattr(moduleInstance, 'PARTS_TO_OUTPUTS'):
                pto = moduleInstance.PARTS_TO_OUTPUTS
            else:
                pto = None
            
            # and store it in our internal structures
            self._moduleDict[moduleInstance] = metaModule(
                moduleInstance, instanceName, fullName, pti, pto)

            # it's now fully born ;)
            self._halfBornInstanceName = None


	except ImportError:
            self._devide_app.logError(
                genUtils.exceptionToMsgs() +
                ["Unable to import module %s!" % fullName])
	    return None
        
	except Exception, e:
            self._devide_app.logError(
                genUtils.exceptionToMsgs() +
                ["Unable to instantiate module %s: %s" \
                                % (fullName, str(e))])
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
            #if not self.isInstalled() or \
            #       modulePrefix == 'userModules':

            # we've changed the logic of this.  bugs in Installer have been
            # fixed, this shouldn't break things too badly.

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
        """Returns True if devide is running from an Installed state.
        Installed of course refers to being installed with Gordon McMillan's
        Installer.  This can be used by devide modules to determine whether
        they should use reload or not.
        """
        return hasattr(modules, '__importsub__')

    def executeModule(self, meta_module, part=0):
        """Execute module instance.

        Important: this method does not result in data being transferred
        after the execution, it JUST performs the module execution.  This
        method is called by the scheduler during network execution.  No
        other call should be used to execute a single module!
        
        @param instance: module instance to be executed.
        @raise moduleManagerException: this exception is raised with an
        informative error string if a module fails to execute.
        @return: Nothing.
        """

        try:
            # this goes via the metaModule so that time stamps and the
            # like are correctly reported
            meta_module.executeModule(part)

            # some modules don't raise exceptions, but rather set an error
            # flag in the moduleManager.
            if self._noExcModuleExecError:
                # so we turn these into an error message
                msgs = self._noExcModuleExecError[:]
                # remembering to zero the error messages
                self._noExcModuleExecError = []
                # and then raise an exception
                raise Exception('\n'.join(msgs))
            
        except Exception, e:
            # get details about the errored module
            instanceName = meta_module.instanceName
            moduleName = meta_module.instance.__class__.__name__

            # and raise the relevant exception
            es = 'Unable to execute part %d of module %s (%s): %s' \
                 % (part, instanceName, moduleName, str(e))
                 
            # we use the three argument form so that we can add a new
            # message to the exception but we get to see the old traceback
            # see: http://docs.python.org/ref/raise.html
            raise moduleManagerException, es, sys.exc_info()[2]
        
            
    def executeNetwork(self, startingModule=None):
        """Execute local network in order, starting from startingModule.

        This is a utility method used by moduleUtils to bind to the Execute
        control found on must module UIs.  We are still in the process
        of formalising the concepts of networks vs. groups of modules.
        Eventually, networks will be grouped by process node and whatnot.

        @todo: integrate concept of startingModule.
        """

        # convert all metaModules to schedulerModules
        sms = self._devide_app.scheduler.metaModulesToSchedulerModules(
            self._moduleDict.values())

        print "STARTING network execute ----------------------------"
        print time.ctime()
        try:
            self._devide_app.scheduler.executeModules(sms)

        except Exception, e:
            # we are directly reporting the error, as this is used by
            # a utility function that is too compact to handle an
            # exception by itself.  Might change in the future.
            emsgs = genUtils.exceptionToMsgs()
            self._devide_app.logError(emsgs + [str(e)])

        print "ENDING network execute ------------------------------"
			      
    def viewModule(self, instance):
        instance.view()
    
    def deleteModule(self, instance):
        """Destroy module.

        This will disconnect all module inputs and outputs and call the
        close() method.  This method is used by the graphEditor and by
        the close() method of the moduleManager.

        @raise moduleManagerException: if an error occurs during module
        deletion.
        """
        
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

        # remove the instance from the markedModules (if it's present)
        # 1. first find all keys that point to it
        mmKeys = [mmItem[0] for mmItem in self._markedModules.items()
                  if mmItem[1] == instance]
        # 2. remove all of em
        for mmKey in mmKeys:
            del self._markedModules[mmKey]

        # get details about the module (we might need this later)
        meta_module = self._moduleDict[instance]
        instanceName = meta_module.instanceName
        moduleName = meta_module.instance.__class__.__name__
        
        # store autoexecute, then disable
        ae = self.auto_execute
        self.auto_execute = False

        try:
            try:
                # now we can finally call close on the instance
                instance.close()

            finally:
                # do the following in all cases:
                # 1. remove module from our dict
                del self._moduleDict[instance]
                # 2. reset auto_execute mode
                self.auto_execute = ae
                # the exception will now be re-raised if there was one
                # to begin with.

        except Exception, e:
            # we're going to re-raise the exception: this method could be
            # called by other parties that need to do alternative error
            # handling

            # create new exception message
            es = 'Error calling close() on module %s (%s): %s' \
                 % (part, instanceName, moduleName, str(e))
                 
            # we use the three argument form so that we can add a new
            # message to the exception but we get to see the old traceback
            # see: http://docs.python.org/ref/raise.html
            raise moduleManagerException, es, sys.exc_info()[2]

    def connectModules(self, output_module, output_idx,
                        input_module, input_idx):
        """Connect output_idx'th output of provider output_module to
        input_idx'th input of consumer input_module.  If an error occurs
        during connection, an exception will be raised.

        @param output_module: This is a module instance.
        """

        # record connection (this will raise an exception if the input
        # is already occupied)
        self._moduleDict[input_module].connectInput(
            input_idx, output_module, output_idx)

        # record connection on the output of the producer module
        # this will also initialise the transfer times
        self._moduleDict[output_module].connectOutput(
            output_idx, input_module, input_idx)

	
    def disconnectModules(self, input_module, input_idx):
        """Disconnect a consumer module from its provider.

        This method will disconnect input_module from its provider by
        disconnecting the link between the provider and input_module at
        the input_idx'th input port of input_module.

        @todo: factor parts of this out into the metaModule.
        FIXME: continue here...  (we can start converting some of
        the modules to shallow copy their data; especially the slice3dVWR
        is a problem child.)
        """

	input_module.setInput(input_idx, None)

        # trace it back to our supplier, and tell it that it has one
        # less consumer (if we even HAVE a supplier on this port)
        s = self._moduleDict[input_module].inputs[input_idx]
        if s:
            supp = s[0]
            suppOutIdx = s[1]

            self._moduleDict[supp].disconnectOutput(
                suppOutIdx, input_module, input_idx)

        # indicate to the meta data that this module doesn't have an input
        # anymore
        self._moduleDict[input_module].disconnectInput(input_idx)

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
                    newModule.setConfig(configCopy)
                except Exception, e:
                    # it could be a module with no defined config logic
                    genUtils.logWarning(
                        'Could not restore state/config to module %s: %s' %
                        (newModule.__class__.__name__, e))
                
                # try to rename the module to the pickled unique instance name
                # if this name is already taken, use the generated unique instance
                # name
                self.renameModule(newModule,pmsTuple[1].instanceName)
                
                # and record that it's been recreated (once again keyed
                # on the OLD unique instance name)
                newModulesDict[pmsTuple[1].instanceName] = newModule

        # now we're going to connect all of the successfully created
        # modules together; we iterate DOWNWARDS through the different
        # consumerTypes
        
        newConnections = []
        for connectionType in range(max(self.consumerTypeTable.values()) + 1):
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

        # now do the POST connection module config!
        for oldInstanceName,newModuleInstance in newModulesDict.items():
            # retrieve the pickled module state
            pms = pmsDict[oldInstanceName]
            # take care to deep copy the config
            configCopy = copy.deepcopy(pms.moduleConfig)

            # now try to call setConfigPostConnect
            try:
                newModuleInstance.setConfigPostConnect(configCopy)
            except AttributeError:
                pass
            except Exception, e:
                # it could be a module with no defined config logic
                genUtils.logWarning(
                    'Could not restore post connect state/config to module '
                    '%s: %s' % (newModuleInstance.__class__.__name__, e))
                


        # we return a dictionary, keyed on OLD pickled name with value
        # the newly created module-instance and a list with the connections
        return (newModulesDict, newConnections)

    def requestAutoExecuteNetwork(self, moduleInstance):
        """Method that can be called by an interaction/view module to
        indicate that some action by the user should result in a network
        update.  The execution will only be performed if the
        AutoExecute mode is active.
        """

        if self.auto_execute:
            print "auto_execute ##### #####"
            self.executeNetwork()

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
                except AttributeError, e:
                    genUtils.logWarning(
                        'Could not extract state (config) from module %s: %s' \
                        % (moduleInstance.__class__.__name__, str(e)))

                    # if we can't get a config, we pickle a default
                    pms.moduleConfig = defaultConfigClass()
                    
                #pms.moduleName = moduleInstance.__class__.__name__
                # we need to store the complete module name
                # we could also get this from meta_module.module_name
                pms.moduleName = moduleInstance.__class__.__module__

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
                        moduleClassName = \
                                        outputConnection[0].__class__.__name__
                        
                        if moduleClassName in self.consumerTypeTable:
                            connectionType = self.consumerTypeTable[
                                moduleClassName]
                        else:
                            connectionType = 1
                            # FIXME: we still have to check for 0: iterate
                            # through all inputs, check that none of the
                            # supplier modules are in the list that we're
                            # going to pickle

                        print '%s has connection type %d' % \
                              (outputConnection[0].__class__.__name__,
                               connectionType)
                        
                        connection = pickledConnection(
                            mModule.instanceName, outputIdx,
                            self._moduleDict[outputConnection[0]].instanceName,
                            outputConnection[1],
                            connectionType)
                                                       
                        connectionList.append(connection)

        return (pmsDict, connectionList)

    def genericProgressCallback(self, progressObject,
                                progressObjectName, progress, progressText):
        """progress between 0.0 and 1.0.
        """

        
        if self._inProgressCallback.testandset():

            # first check if execution has been disabled
            # the following bit of code is risky: the ITK to VTK bridges
            # seem to be causing segfaults when we abort too soon
#             if not self._executionEnabled:
#                 try:
#                     progressObject.SetAbortExecute(1)
#                 except Exception:
#                     pass

#                 try:
#                     progressObject.SetAbortGenerateData(1)
#                 except Exception:
#                     pass
                    
#                 progress = 1.0
#                 progressText = 'Execution ABORTED.'
            
            progressP = progress * 100.0
            fullText = '%s: %s' % (progressObjectName, progressText)
            if abs(progressP - 100.0) < 0.01:
                # difference smaller than a hundredth
                fullText += ' [DONE]'

            self.setProgress(progressP, fullText)
            self._inProgressCallback.unlock()
    

    def getConsumers(self, meta_module):
        """Determine meta modules that are connected to the outputs of
        meta_module.

        This method is called by: scheduler, self.recreate_module_in_place.

        @todo: this should be part of the metaModule code, as soon as
        the metaModule inputs and outputs are of type metaModule and not
        instance.

        @param instance: module instance of which the consumers should be
        determined.
        @return: list of tuples, each consisting of (this module's output
        index, the consumer meta module, the consumer input index)
        """

        consumers = []

        # get outputs from metaModule: this is a list of list of tuples
        # outer list has number of outputs elements
        # inner lists store consumer modules for that output
        # tuple contains (consumerModuleInstance, consumerInputIdx)
        outputs = meta_module.outputs

        for outputIdx in range(len(outputs)):
            output = outputs[outputIdx]
            for consumerInstance, consumerInputIdx in output:
                consumerMetaModule = self._moduleDict[consumerInstance]
                consumers.append(
                    (outputIdx, consumerMetaModule, consumerInputIdx))

        return consumers

    def getProducers(self, meta_module):
        """Return a list of meta modules, output indices and the input
        index through which they supply 'meta_module' with data.

        @todo: this should be part of the metaModule code, as soon as
        the metaModule inputs and outputs are of type metaModule and not
        instance.

        @param meta_module: consumer meta module.
        @return: list of tuples, each tuple consists of producer meta module
        and output index as well as input index of the instance input that
        they connect to.
        """
        
        # inputs is a list of tuples, each tuple containing moduleInstance
        # and outputIdx of the producer/supplier module; if the port is
        # not connected, that position in inputs contains "None"
        inputs = meta_module.inputs

        producers = []
        for i in range(len(inputs)):
            pTuple = inputs[i]
            if pTuple is not None:
                # unpack
                pInstance, pOutputIdx = pTuple
                pMetaModule = self._moduleDict[pInstance]
                # and store
                producers.append((pMetaModule, pOutputIdx, i))

        return producers

    def setModified(self, moduleInstance):
        """Changed modified ivar in metaModule.

        This ivar is used to determine whether moduleInstance needs to be
        executed to become up to date.  It should be set whenever changes
        are made that dirty the module state, for example parameter changes
        or topology changes.

        @param moduleInstance: the instance whose modified state sbould be
        changed.
        @param value: the new value of the modified ivar, True or False.
        """
        
        self._moduleDict[moduleInstance].modified = value
        
    def setProgress(self, progress, message, noTime=False):
        """Progress is in percent.
        """
        self._devide_app.setProgress(progress, message, noTime)

    def _makeUniqueInstanceName(self, instanceName=None):
        """Ensure that instanceName is unique or create a new unique
        instanceName.

        If instanceName is None, a unique one will be created.  An
        instanceName (whether created or passed) will be permuted until it
        unique and then returned.
        """
        
        # first we make sure we have a unique instance name
        if not instanceName:
            instanceName = "dvm%d" % (len(self._moduleDict),)

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


    def markModule(self, instance, name):
        """Add instance to self._markedModules dictionary with name as
        key.  Anything other than a module instance will not be added.

        
        """

        if instance in self._moduleDict:
            self._markedModules[name] = instance

    def getMarkedModule(self, name):
        """Return module instance from self._markedModules with key == name.

        If the key does not exist, returns None.
        """

        if name in self._markedModules:
            return self._markedModules[name]
        else:
            return None

    def renameModule(self, instance, name):
        """Rename a module in the module dictionary
        """

        # if we get a duplicate name, we either add (%d) after, or replace
        # the existing %d with something that makes it all unique...
        mo = re.match('(.*)\s+\(([1-9]+)\)', name)
        if mo:
            basename = mo.group(1)
            i = int(mo.group(2)) + 1
        else:
            basename = name
            i = 1
        
        while (self.getInstance(name) != None):
            # add a number (%d) until the name is unique
            name = '%s (%d)' % (basename, i)
            i += 1

        try:
            # get the metaModule and rename it.
            self._moduleDict[instance].instanceName = name
        except Exception:
            return False

        # everything proceeded according to plan.        
        return True

    def modifyModule(self, moduleInstance, part=0):
        """Call this whenever module state has changed in such a way that
        necessitates a re-execution, for instance when parameters have been
        changed or when new input data has been transferred.
        """

        self._moduleDict[moduleInstance].modify(part)

    def recreate_module_in_place(self, meta_module):
        """Destroy, create and reconnect a module in place.

        This function works but is not being used at the moment.  It was
        intended for graphEditor-driven module reloading, but it turned out
        that implementing that in the graphEditor was easier.  I'm keeping
        this here for reference purposes.
        
        @param meta_module: The module that will be destroyed.
        @returns: new meta_module.
        """

        # 1. store input and output connections, module name, module state
        #################################################################

        # prod_tuple contains a list of (prod_meta_module, output_idx,
        # input_idx) tuples
        prod_tuples = self.getProducers(meta_module)
        # cons_tuples contains a list of (output_index, consumer_meta_module,
        # consumer input index)
        cons_tuples = self.getConsumers(meta_module)
        # store the instance name
        instance_name = meta_module.instanceName
        # and the full module spec name
        full_name = meta_module.module_name
        # and get the module state (we make a deep copy just in case)
        module_config = copy.deepcopy(meta_module.instance.getConfig())

        # 2. instantiate a new one and give it its old config
        ###############################################################
        # because we instantiate the new one first, if this instantiation
        # breaks, an exception will be raised and no harm will be done,
        # we still have the old one lying around

        # instantiate
        new_instance = self.createModule(full_name, instance_name)
        # and give it its old config back
        new_instance.setConfig(module_config)

        # 3. delete the old module
        #############################################################
        self.deleteModule(meta_module.instance)

        # 4. now rename the new module
        #############################################################

        # find the corresponding new meta_module
        meta_module = self._moduleDict[new_instance]
        # give it its old name back
        meta_module.instanceName = instance_name

        # 5. connect it up
        #############################################################
        for producer_meta_module, output_idx, input_idx in prod_tuples:
            self.connectModules(
                producer_meta_module.instance, output_idx,
                new_instance, input_idx)

        for output_idx, consumer_meta_module, input_idx in cons_tuples:
            self.connectModules(
                new_instance, output_idx,
                consumer_meta_module.instance, input_idx)

        # we should be done now
        return meta_module
        

    def shouldExecuteModule(self, meta_module, part=0):

        """Determine whether moduleInstance requires execution to become
        up to date.

        Execution is required when the module is new or when the user has made
        parameter or introspection changes.  All of these conditions should be
        indicated by calling L{moduleManager.modify(instance)}.

        @return: True if execution required, False if not.
        """

        return meta_module.shouldExecute(part)

    def shouldTransferOutput(
        self,
        meta_module, output_idx, consumer_meta_module, consumer_input_idx):
        
        """Determine whether output data has to be transferred from
        moduleInstance via output outputIndex to module consumerInstance.

        Output needs to be transferred if:
         - moduleInstance has new or changed output
         - consumerInstance does not have the data anymore / yet

        @return: True if output should be transferred, False if not.
        """
        
        return meta_module.shouldTransferOutput(
            output_idx, consumer_meta_module, consumer_input_idx)

        
    def transferOutput(
        self,
        meta_module, output_idx, consumer_meta_module, consumer_input_idx):

        """Transfer output data from moduleInstance to the consumer modules
        connected to its specified output indexes.

        This will be called by the scheduler right before execution to
        transfer the given output from moduleInstance instance to the correct
        input on the consumerInstance.  In general, this is only done if
        shouldTransferOutput is true, so the number of unnecessary transfers
        should be minimised.

        This method is in moduleManager and not in metaModule because it
        involves more than one metaModule.

        @param moduleInstance: producer module whose output data must be
        transferred.
        @param outputIndex: only output data produced by this output will
        be transferred.
        @param consumerInstance: only data going to this instance will be
        transferred.
        @param consumerInputIdx: data enters consumerInstance via this input
        port.

        @raise moduleManagerException: if an error occurs getting the data
        from or transferring it to a new module.
        """

        #print 'transferring data %s:%d' % (moduleInstance.__class__.__name__,
        #                                   outputIndex)

        # double check that this connection already exists

        consumer_instance = consumer_meta_module.instance
        if meta_module.findConsumerInOutputConnections(
            output_idx, consumer_instance, consumer_input_idx) == -1:

            raise Exception, 'moduleManager.transferOutput called for ' \
                  'connection that does not exist.'
        
        try:
            # get data from producerModule output
            od = meta_module.instance.getOutput(output_idx)

            # some modules don't raise exceptions, but rather set an error
            # flag in the moduleManager.
            if self._noExcModuleExecError:
                # so we turn these into an error message
                msgs = self._noExcModuleExecError[:]
                # remembering to zero the error messages
                self._noExcModuleExecError = []
                # and then raise an exception
                raise Exception('\n'.join(msgs))
            
        except Exception, e:
            # get details about the errored module
            instanceName = meta_module.instanceName
            moduleName = meta_module.instance.__class__.__name__

            # and raise the relevant exception
            es = 'Faulty transferOutput (getOutput on module %s (%s)): %s' \
                 % (instanceName, moduleName, str(e))
                 
            # we use the three argument form so that we can add a new
            # message to the exception but we get to see the old traceback
            # see: http://docs.python.org/ref/raise.html
            raise moduleManagerException, es, sys.exc_info()[2]
        
        

        # experiment here with making shallowcopies if we're working with
        # VTK data.
        # TODO: somehow this should be part of one of the moduleKits
        # or some other module-related pluggable logic.
        if od and hasattr(od, 'GetClassName') and hasattr(od, 'ShallowCopy'):
            nod = od.__class__()
            nod.ShallowCopy(od)
            od = nod
        
        try:
            # set on consumerInstance input
            consumer_meta_module.instance.setInput(consumer_input_idx, od)

            # some modules don't raise exceptions, but rather set an error
            # flag in the moduleManager.
            if self._noExcModuleExecError:
                # so we turn these into an error message
                msgs = self._noExcModuleExecError[:]
                # remembering to zero the error messages
                self._noExcModuleExecError = []
                # and then raise an exception
                raise Exception('\n'.join(msgs))
            
        except Exception, e:
            # get details about the errored module
            instanceName = consumer_meta_module.instanceName
            moduleName = consumer_meta_module.instance.__class__.__name__

            # and raise the relevant exception
            es = 'Faulty transferOutput (setInput on module %s (%s)): %s' \
                 % (instanceName, moduleName, str(e))

            # we use the three argument form so that we can add a new
            # message to the exception but we get to see the old traceback
            # see: http://docs.python.org/ref/raise.html
            raise moduleManagerException, es, sys.exc_info()[2]
        

        # record that the transfer has just happened
        meta_module.timeStampTransferTime(
            output_idx, consumer_instance, consumer_input_idx)

        # also invalidate the consumerModule: it should re-execute when
        # a transfer has been made.  We only invalidate the part that
        # takes responsibility for that input.
        part = consumer_meta_module.getPartForInput(consumer_input_idx)
        consumer_meta_module.modify(part)

        # execute on change
        # we probably shouldn't automatically execute here... transfers
        # mean that some sort of network execution is already running
