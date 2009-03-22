# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

import ConfigParser
import sys, os, fnmatch
import re
import copy
import gen_utils
import glob
from meta_module import MetaModule
import modules
import mutex
from random import choice
from module_base import DefaultConfigClass
import time
import types
import traceback

# some notes with regards to extra module state/logic required for scheduling
# * in general, execute_module()/transfer_output()/etc calls do exactly that
#   when called, i.e. they don't automatically cache.  The scheduler should
#   take care of caching by making the necessary isModified() or
#   shouldTransfer() calls.  The reason for this is so that the module
#   actions can be forced
#

# notes with regards to execute on change:
# * devide.py should register a "change" handler with the ModuleManager.
#   I've indicated places with "execute on change" where I think this
#   handler should be invoked.  devide.py can then invoke the scheduler.

#########################################################################
class ModuleManagerException(Exception):
    pass
    
#########################################################################
class ModuleSearch:
    """Class for doing relative fast searches through module metadata.

    @author Charl P. Botha <http://cpbotha.net/>
    """
    
    def __init__(self):
        # dict of dicts of tuple, e.g.:
        # {'isosurface' : {('contour', 'keywords') : 1,
        #                  ('marching', 'help') : 1} ...
        self.search_dict = {}
        self.previous_partial_text = ''
        self.previous_results = None

    def build_search_index(self, available_modules, available_segments):
        """Build search index given a list of available modules and segments.

        @param available_modules: available modules dictionary from module
        manager with module metadata classes as values.
        @param available_segments: simple list of segments.
        """
        
        self.search_dict.clear()

        def index_field(index_name, mi_class, field_name, split=False):
            try:
                field = getattr(mi_class, field_name)
                
            except AttributeError:
                pass
            else:
                if split:
                    iter_list = field.split()
                else:
                    iter_list = field
                    
                for w in iter_list:
                    wl = w.lower()
                    if wl not in self.search_dict:
                        self.search_dict[wl] = {(index_name,
                                                 field_name) : 1}
                    else:
                        self.search_dict[wl][(index_name,
                                              field_name)] = 1

        for module_name in available_modules:
            mc = available_modules[module_name]
            index_name = 'module:%s' % (module_name,)
            short_module_name = mc.__name__.lower()

            if short_module_name not in self.search_dict:
                self.search_dict[short_module_name] = {(index_name, 'name') :
                1}
            else:
                # we don't have to increment, there can be only one unique
                # complete module_name
                self.search_dict[short_module_name][(index_name, 'name')] = 1
                
            index_field(index_name, mc, 'keywords')
            index_field(index_name, mc, 'help', True)

        for segment_name in available_segments:
            index_name = 'segment:%s' % (segment_name,)
            # segment name's are unique by definition (complete file names)
            self.search_dict[segment_name] = {(index_name, 'name') : 1}

    def find_matches(self, partial_text):
        """Do partial text (containment) search through all module names,
        help and keywords.

        Simple caching is currently done.  Each space-separated word in
        partial_text is searched for and results are 'AND'ed.

        @returns: a list of unique tuples consisting of (modulename,
        where_found) where where_found is 'name', 'keywords' or 'help'
        """

        # cache results in case the user asks for exactly the same
        if partial_text == self.previous_partial_text:
            return self.previous_results

        partial_words = partial_text.lower().split()

        # dict mapping from full.module.name -> {'where_found' : 1, 'wf2' : 1}
        # think about optimising this with a bit mask rather; less flexible
        # but saves space and is at least as fast.

        def find_one_word(search_word):
            """Searches for all partial / containment matches with
            search_word.

            @returns: search_results dict mapping from module name to
            dictionary with where froms as keys and 1s as values.
            
            """
            search_results = {}
            for w in self.search_dict:
                if w.find(search_word) >= 0:
                    # we can have partial matches with more than one key
                    # returning the same location, so we stuff results in a 
                    # dict too to consolidate results
                    for k in self.search_dict[w].keys():
                        # k[1] is where_found, k[0] is module_name
                        if k[0] not in search_results:
                            search_results[k[0]] = {k[1] : 1}
                                
                        else:
                            search_results[k[0]][k[1]] = 1

            return search_results

        # search using each of the words in the given list
        search_results_list = []
        for search_word in partial_words:
            search_results_list.append(find_one_word(search_word))

        # if more than one word, combine the results;
        # a module + where_from result is only shown if ALL words occur in
        # that specific module + where_from.

        sr0 = search_results_list[0]
        srl_len = len(search_results_list)
        if srl_len > 1:
            # will create brand-new combined search_results dict
            search_results = {}

            # iterate through all module names in the first word's results
            for module_name in sr0:
                # we will only process a module_name if it occurs in the
                # search results of ALL search words
                all_found = True
                for sr in search_results_list[1:]:
                    if module_name not in sr:
                        all_found = False
                        break

                # now only take results where ALL search words occur
                # in the same where_from of a specific module
                if all_found:
                    temp_finds = {}
                    for sr in search_results_list:
                        # sr[module_name] is a dict with where_founds as keys
                        # by definition (dictionary) all where_founds are
                        # unique per sr[module_name]
                        for i in sr[module_name].keys():
                            if i in temp_finds:
                                temp_finds[i] += 1
                            else:
                                temp_finds[i] = 1

                    # extract where_froms for which the number of hits is
                    # equal to the number of words.
                    temp_finds2 = [wf for wf in temp_finds.keys() if
                                   temp_finds[wf] == srl_len]

                    # make new dictionary from temp_finds2 list as keys,
                    # 1 as value
                    search_results[module_name] = dict.fromkeys(temp_finds2,1)

        else:
            # only a single word was searched for.
            search_results = sr0
            
                    
        self.previous_partial_text = partial_text
        rl = search_results
        self.previous_results = rl
        return rl
        

#########################################################################
class PickledModuleState:
    def __init__(self):
        self.module_config = DefaultConfigClass()
        # e.g. modules.Viewers.histogramSegment
        self.module_name = None
        # this is the unique name of the module, e.g. dvm15
        self.instance_name = None

#########################################################################
class PickledConnection:
    def __init__(self, source_instance_name=None, output_idx=None,
                 target_instance_name=None, input_idx=None, connection_type=None):
        
        self.source_instance_name = source_instance_name
        self.output_idx = output_idx
        self.target_instance_name = target_instance_name
        self.input_idx = input_idx
        self.connection_type = connection_type

#########################################################################
class ModuleManager:
    """This class in responsible for picking up new modules in the modules 
    directory and making them available to the rest of the program.

    @todo: we should split this functionality into a ModuleManager and
    networkManager class.  One ModuleManager per processing node,
    global networkManager to coordinate everything.

    @todo: ideally, ALL module actions should go via the MetaModule.
    
    @author: Charl P. Botha <http://cpbotha.net/>
    """
    
    def __init__(self, devide_app):
        """Initialise module manager by fishing .py devide modules from
        all pertinent directories.
        """
	
        self._devide_app = devide_app
        # module dictionary, keyed on instance... cool.
        # values are MetaModules
        self._module_dict = {}

        appdir = self._devide_app.get_appdir()
        self._modules_dir = os.path.join(appdir, 'modules')
        #sys.path.insert(0,self._modules_dir)
        
        self._userModules_dir = os.path.join(appdir, 'userModules')

        ############################################################
        # initialise module Kits - Kits are collections of libraries
        # that modules can depend on.  The Kits also make it possible
        # for us to write hooks for when these libraries are imported
        import module_kits
        module_kits.load(self)

        # binding to module that can be used without having to do
        # import module_kits
        self.module_kits = module_kits
                    

        ##############################################################

        self.module_search = ModuleSearch()
        
        # make first scan of available modules
        self.scan_modules()

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
        # callback... (there SHOULD only be ONE ModuleManager instance)
        self._inProgressCallback = mutex.mutex()

    def refresh_module_kits(self):
        """Go through list of imported module kits, reload each one, and
        also call its refresh() method if available.

        This means a kit author can work on a module_kit and just refresh
        when she wants her changes to be available.  However, the kit must
        have loaded successfully at startup, else no-go.
        """
        
        for module_kit in self.module_kits.module_kit_list:
            kit = getattr(self.module_kits, module_kit)
            try:
                refresh_method = getattr(kit, "refresh")
            except AttributeError:
                pass
            else:
                try:
                    reload(kit)
                    refresh_method()                
                except Exception, e:
                    self._devide_app.log_error_with_exception(
                        'Unable to refresh module_kit %s: '
                        '%s.  Continuing...' %
                        (module_kit, str(e)))
                else:
                    self.set_progress(100, 'Refreshed %s.' % (module_kit,))
                    
    def close(self):
        """Iterates through each module and closes it.

        This is only called during devide application shutdown.
        """
        self.delete_all_modules()

    def delete_all_modules(self):
        """Deletes all modules.

        This is usually only called during the offline mode of operation.  In
        view mode, the GraphEditor takes care of the deletion of all networks.
        """
        
        # this is fine because .items() makes a copy of the dict
        for mModule in self._module_dict.values():

            print "Deleting %s (%s) >>>>>" % \
                  (mModule.instance_name,
                   mModule.instance.__class__.__name__)
                   
            try:
                self.delete_module(mModule.instance)
            except Exception, e:
                # we can't allow a module to stop us
                print "Error deleting %s (%s): %s" % \
                      (mModule.instance_name,
                       mModule.instance.__class__.__name__,
                       str(e))
                print "FULL TRACE:"
                traceback.print_exc()

    def apply_module_view_to_logic(self, instance):
        """Interface method that can be used by clients to transfer module
        view to underlying logic.

        This is called by module_utils (the ECASH button handlers) and thunks
        through to the relevant MetaModule call.
        """

        mModule = self._module_dict[instance]

        try:
            # these two MetaModule wrapper calls will take care of setting
            # the modified flag / time correctly

            if self._devide_app.view_mode:
                # only in view mode do we call this transfer
                mModule.view_to_config()
                
            mModule.config_to_logic()

            # we round-trip so that view variables that are dependent on
            # the effective changes to logic and/or config can update
            instance.logic_to_config()

            if self._devide_app.view_mode:
                instance.config_to_view()

        except Exception, e:
            # we are directly reporting the error, as this is used by
            # a utility function that is too compact to handle an
            # exception by itself.  Might change in the future.
            self._devide_app.log_error_with_exception(str(e))

    def sync_module_logic_with_config(self, instance):
        """Method that should be called during __init__ for all (view and
        non-view) modules, after the config structure has been set.

        In the view() method, or after having setup the view in view-modules,
        also call syncModuleViewWithLogic()
        """
        
        instance.config_to_logic()
        instance.logic_to_config()

    def sync_module_view_with_config(self, instance):
        """If DeVIDE is in view model, transfor config information to view
        and back again.  This is called AFTER sync_module_logic_with_config(),
        usually in the module view() method after createViewFrame().
        """
        
        if self._devide_app.view_mode:
            # in this case we don't round trip, view shouldn't change
            # things that affect the config.
            instance.config_to_view()

    def sync_module_view_with_logic(self, instance):
        """Interface method that can be used by clients to transfer config
        information from the underlying module logic (model) to the view.

        At the moment used by standard ECASH handlers.
        """

        try:
            instance.logic_to_config()

            # we only do the view transfer if DeVIDE is in the correct mode
            if self._devide_app.view_mode:
                instance.config_to_view()
            
        except Exception, e:
            # we are directly reporting the error, as this is used by
            # a utility function that is too compact to handle an
            # exception by itself.  Might change in the future.
            self._devide_app.log_error_with_exception(str(e))

    syncModuleViewWithLogic = sync_module_view_with_logic

    def blockmodule(self, meta_module):
        meta_module.blocked = True

    def unblockmodule(self, meta_module):
        meta_module.blocked = False

    def log_error(self, message):
        """Convenience method that can be used by modules.
        """
        self._devide_app.log_error(message)

    def log_error_list(self, message_list):
        self._devide_app.log_error_list(message_list)

    def log_error_with_exception(self, message):
        """Convenience method that can be used by modules.
        """
        self._devide_app.log_error_with_exception(message)

    def log_info(self, message):
        """Convenience method that can be used by modules.
        """
        self._devide_app.log_info(message)

    def log_message(self, message):
        """Convenience method that can be used by modules.
        """
        self._devide_app.log_message(message)

    def log_warning(self, message):
        """Convenience method that can be used by modules.
        """
        self._devide_app.log_warning(message)


    def scan_modules(self):
        """(Re)Check the modules directory for *.py files and put them in
        the list self.module_files.
        """

        # this is a dict mapping from full module name to the classes as
        # found in the module_index.py files
        self._available_modules = {}
        appDir = self._devide_app.get_appdir()
        # module path without trailing slash
        modulePath = self.get_modules_dir()

        # search through modules hierarchy and pick up all module_index files
        ####################################################################

        module_indices = []

        def miwFunc(arg, dirname, fnames):
            """arg is top-level module path.
            """
            module_path = arg
            for fname in fnames:
                mi_full_name = os.path.join(dirname, fname)
                if not fnmatch.fnmatch(fname, 'module_index.py'):
                    continue

                # e.g. /viewers/module_index
                mi2 = os.path.splitext(
                        mi_full_name.replace(module_path, ''))[0]
                # e.g. .viewers.module_index
                mim = mi2.replace(os.path.sep, '.')
                # remove . before
                if mim.startswith('.'):
                    mim = mim[1:]

                # special case: modules in the central devide
                # module dir should be modules.viewers.module_index
                # this is mostly for backward compatibility
                if module_path == modulePath:
                    mim = 'modules.%s' % (mim)

                module_indices.append(mim)

        os.path.walk(modulePath, miwFunc, arg=modulePath)

        for emp in self.get_app_main_config().extra_module_paths:
            # make sure there are no extra spaces at the ends, as well
            # as normalize and absolutize path (haha) for this
            # platform
            emp = os.path.abspath(emp.strip())
            if emp and os.path.exists(emp):
                # make doubly sure we only process an EMP if it's
                # really there
                if emp not in sys.path:
                    sys.path.insert(0,emp)

                os.path.walk(emp, miwFunc, arg=emp)

        # iterate through the moduleIndices, building up the available
        # modules list.
        import module_kits # we'll need this to check available kits
        failed_mis = {}
        for mim in module_indices:
            # mim is importable module_index spec, e.g.
            # modules.viewers.module_index

            # if this thing was imported before, we have to remove it, else
            # classes that have been removed from the module_index file
            # will still appear after the reload.
            if mim in sys.modules:
                del sys.modules[mim]

            try:
                # now we can import
                __import__(mim, globals(), locals())
                
            except Exception, e:
                # make a list of all failed moduleIndices
                failed_mis[mim] = sys.exc_info()
                msgs = gen_utils.exceptionToMsgs()

                # and log them as mesages
                self._devide_app.log_info(
                    'Error loading %s: %s.' % (mim, str(e)))

                for m in msgs:
                    self._devide_app.log_info(m.strip(), timeStamp=False)

                # we don't want to throw an exception here, as that would
                # mean that a singe misconfigured module_index file can
                # prevent the whole scan_modules process from completing
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
                        self._available_modules[module_name] = c


        # we should move this functionality to the graphEditor.  "segments"
        # are _probably_ only valid there... alternatively, we should move
        # the concept here

        segmentList = []
        def swFunc(arg, dirname, fnames):
            segmentList.extend([os.path.join(dirname, fname)
                                for fname in fnames
                                if fnmatch.fnmatch(fname, '*.dvn')])

        os.path.walk(os.path.join(appDir, 'segments'), swFunc, arg=None)

        # this is purely a list of segment filenames
        self.availableSegmentsList = segmentList

        # self._available_modules is a dict keyed on module_name with
        # module description class as value
        self.module_search.build_search_index(self._available_modules,
                                              self.availableSegmentsList)

        # report on accumulated errors - this is still a non-critical error
        # so we don't throw an exception.
        if len(failed_mis) > 0:
            failed_indices = '\n'.join(failed_mis.keys())
            self._devide_app.log_error(
                'The following module indices failed to load '
                '(see message log for details): \n%s' \
                % (failed_indices,))

        self._devide_app.log_info(
            '%d modules and %d segments scanned.' %
            (len(self._available_modules), len(self.availableSegmentsList)))
        
    ########################################################################

    def get_appdir(self):
        return self._devide_app.get_appdir()

    def get_app_main_config(self):
        return self._devide_app.main_config
	
    def get_available_modules(self):
        """Return the available_modules, a dictionary keyed on fully qualified
        module name (e.g. modules.Readers.vtiRDR) with values the classes
        defined in module_index files.
        """
        
        return self._available_modules


    def get_instance(self, instance_name):
        """Given the unique instance name, return the instance itself.
        If the module doesn't exist, return None.
        """

        found = False
        for instance, mModule in self._module_dict.items():
            if mModule.instance_name == instance_name:
                found = True
                break

        if found:
            return mModule.instance

        else:
            return None

    def get_instance_name(self, instance):
        """Given the actual instance, return its unique instance.  If the
        instance doesn't exist in self._module_dict, return the currently
        halfborn instance.
        """

        try:
            return self._module_dict[instance].instance_name
        except Exception:
            return self._halfBornInstanceName

    def get_meta_module(self, instance):
        """Given an instance, return the corresponding meta_module.

        @param instance: the instance whose meta_module should be returned.
        @return: meta_module corresponding to instance.
        @raise KeyError: this instance doesn't exist in the module_dict.
        """
        return self._module_dict[instance]

    def get_modules_dir(self):
        return self._modules_dir

    def get_module_view_parent_window(self):
        # this could change
        return self.get_module_view_parent_window()

    def get_module_spec(self, module_instance):
        """Given a module instance, return the full module spec.
        """
        return 'module:%s' % (module_instance.__class__.__module__,)

    def get_module_view_parent_window(self):
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
    
    def create_module(self, fullName, instance_name=None):
        """Try and create module fullName.

        @param fullName: The complete module spec below application directory,
        e.g. modules.Readers.hdfRDR.

        @return: module_instance if successful.

        @raises ModuleManagerException: if there is a problem creating the
        module.
        """

        if fullName not in self._available_modules:
            raise ModuleManagerException(
                '%s is not available in the current Module Manager / '
                'Kit configuration.' % (fullName,))

        try:
            # think up name for this module (we have to think this up now
            # as the module might want to know about it whilst it's being
            # constructed
            instance_name = self._make_unique_instance_name(instance_name)
            self._halfBornInstanceName = instance_name
            
            # perform the conditional import/reload
            self.import_reload(fullName)
            # import_reload requires this afterwards for safety reasons
            exec('import %s' % fullName)
            # in THIS case, there is a McMillan hook which'll tell the
            # installer about all the devide modules. :)

            ae = self.auto_execute
            self.auto_execute = False

            try:
                # then instantiate the requested class
                module_instance = None
                exec(
                    'module_instance = %s.%s(self)' % (fullName,
                                                      fullName.split('.')[-1]))
            finally:
                # do the following in all cases:
                self.auto_execute = ae

                # if there was an exception, it will now be re-raised

            if hasattr(module_instance, 'PARTS_TO_INPUTS'):
                pti = module_instance.PARTS_TO_INPUTS
            else:
                pti = None

            if hasattr(module_instance, 'PARTS_TO_OUTPUTS'):
                pto = module_instance.PARTS_TO_OUTPUTS
            else:
                pto = None
            
            # and store it in our internal structures
            self._module_dict[module_instance] = MetaModule(
                module_instance, instance_name, fullName, pti, pto)

            # it's now fully born ;)
            self._halfBornInstanceName = None

        except ImportError, e:
            # we re-raise with the three argument form to retain full
            # trace information.
            es = "Unable to import module %s: %s" % (fullName, str(e))
            raise ModuleManagerException, es, sys.exc_info()[2]
        
        except Exception, e:
            es = "Unable to instantiate module %s: %s" % (fullName, str(e))
            raise ModuleManagerException, es, sys.exc_info()[2]

        # return the instance
        return module_instance

    def import_reload(self, fullName):
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
        ModuleManager.import_reloadModule('full.path.to.my.module')
        import full.path.to.my.module
        so that the module is actually brought into the calling namespace.

        import_reload used to return the modulePrefix object, but this has
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
           exec('reload(' + fullName + ')')

        # we need to inject the import into the calling dictionary...
        # importing my.module results in "my" in the dictionary, so we
        # split at '.' and return the object bound to that name
        # return locals()[modulePrefix]
        # we DON'T do this anymore, so that module writers are forced to
        # use an import statement straight after calling import_reload (or
        # somewhere else in the module)

    def isInstalled(self):
        """Returns True if devide is running from an Installed state.
        Installed of course refers to being installed with Gordon McMillan's
        Installer.  This can be used by devide modules to determine whether
        they should use reload or not.
        """
        return hasattr(modules, '__importsub__')

    def execute_module(self, meta_module, part=0, streaming=False):
        """Execute module instance.

        Important: this method does not result in data being transferred
        after the execution, it JUST performs the module execution.  This
        method is called by the scheduler during network execution.  No
        other call should be used to execute a single module!
        
        @param instance: module instance to be executed.
        @raise ModuleManagerException: this exception is raised with an
        informative error string if a module fails to execute.
        @return: Nothing.
        """

        try:
            # this goes via the MetaModule so that time stamps and the
            # like are correctly reported
            meta_module.execute_module(part, streaming)

            
        except Exception, e:
            # get details about the errored module
            instance_name = meta_module.instance_name
            module_name = meta_module.instance.__class__.__name__

            # and raise the relevant exception
            es = 'Unable to execute part %d of module %s (%s): %s' \
                 % (part, instance_name, module_name, str(e))
                 
            # we use the three argument form so that we can add a new
            # message to the exception but we get to see the old traceback
            # see: http://docs.python.org/ref/raise.html
            raise ModuleManagerException, es, sys.exc_info()[2]
        
            
    def execute_network(self, startingModule=None):
        """Execute local network in order, starting from startingModule.

        This is a utility method used by module_utils to bind to the Execute
        control found on must module UIs.  We are still in the process
        of formalising the concepts of networks vs. groups of modules.
        Eventually, networks will be grouped by process node and whatnot.

        @todo: integrate concept of startingModule.
        """

        try:
            self._devide_app.network_manager.execute_network(
                self._module_dict.values())

        except Exception, e:
            # we are directly reporting the error, as this is used by
            # a utility function that is too compact to handle an
            # exception by itself.  Might change in the future.
            self._devide_app.log_error_with_exception(str(e))

			      
    def view_module(self, instance):
        instance.view()
    
    def delete_module(self, instance):
        """Destroy module.

        This will disconnect all module inputs and outputs and call the
        close() method.  This method is used by the graphEditor and by
        the close() method of the ModuleManager.

        @raise ModuleManagerException: if an error occurs during module
        deletion.
        """

        # get details about the module (we might need this later)
        meta_module = self._module_dict[instance]
        instance_name = meta_module.instance_name
        module_name = meta_module.instance.__class__.__name__
        
        # first disconnect all outgoing connections
        inputs = self._module_dict[instance].inputs
        outputs = self._module_dict[instance].outputs

        # outputs is a list of lists of tuples, each tuple containing
        # module_instance and input_idx of the consumer module
        for output in outputs:
            if output:
                # we just want to walk through the dictionary tuples
                for consumer in output:
                    # disconnect all consumers
                    self.disconnect_modules(consumer[0], consumer[1])

        # inputs is a list of tuples, each tuple containing module_instance
        # and output_idx of the producer/supplier module
        for input_idx in range(len(inputs)):
            try:
                # also make sure we fully disconnect ourselves from
                # our producers
                self.disconnect_modules(instance, input_idx)
            except Exception, e:
                # we can't allow this to prevent a destruction, just log
                self.log_error_with_exception(
                    'Module %s (%s) errored during disconnect of input %d. '
                    'Continuing with deletion.' % \
                    (instance_name, module_name, input_idx))
                
            # set supplier to None - so we know it's nuked
            inputs[input_idx] = None

        # we've disconnected completely - let's reset all lists
        self._module_dict[instance].reset_inputsOutputs()

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
                del self._module_dict[instance]
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
                 % (instance_name, module_name, str(e))
                 
            # we use the three argument form so that we can add a new
            # message to the exception but we get to see the old traceback
            # see: http://docs.python.org/ref/raise.html
            raise ModuleManagerException, es, sys.exc_info()[2]

    def connect_modules(self, output_module, output_idx,
                        input_module, input_idx):
        """Connect output_idx'th output of provider output_module to
        input_idx'th input of consumer input_module.  If an error occurs
        during connection, an exception will be raised.

        @param output_module: This is a module instance.
        """

        # record connection (this will raise an exception if the input
        # is already occupied)
        self._module_dict[input_module].connectInput(
            input_idx, output_module, output_idx)

        # record connection on the output of the producer module
        # this will also initialise the transfer times
        self._module_dict[output_module].connectOutput(
            output_idx, input_module, input_idx)

	
    def disconnect_modules(self, input_module, input_idx):
        """Disconnect a consumer module from its provider.

        This method will disconnect input_module from its provider by
        disconnecting the link between the provider and input_module at
        the input_idx'th input port of input_module.

        All errors will be handled internally in this function, i.e. no
        exceptions will be raised.

        @todo: factor parts of this out into the MetaModule.
        FIXME: continue here...  (we can start converting some of
        the modules to shallow copy their data; especially the slice3dVWR
        is a problem child.)
        """

        meta_module = self._module_dict[input_module]
        instance_name = meta_module.instance_name
        module_name = meta_module.instance.__class__.__name__

        try:
            input_module.set_input(input_idx, None)
        except Exception, e:
            # if the module errors during disconnect, we have no choice
            # but to continue with deleting it from our metadata
            # at least this way, no data transfers will be attempted during
            # later network executions.
            self._devide_app.log_error_with_exception(
                'Module %s (%s) errored during disconnect of input %d. '
                'Removing link anyway.' % \
                (instance_name, module_name, input_idx))

        # trace it back to our supplier, and tell it that it has one
        # less consumer (if we even HAVE a supplier on this port)
        s = self._module_dict[input_module].inputs[input_idx]
        if s:
            supp = s[0]
            suppOutIdx = s[1]

            self._module_dict[supp].disconnectOutput(
                suppOutIdx, input_module, input_idx)

        # indicate to the meta data that this module doesn't have an input
        # anymore
        self._module_dict[input_module].disconnectInput(input_idx)

    def deserialise_module_instances(self, pmsDict, connectionList):
        """Given a pickled stream, this method will recreate all modules,
        configure them and connect them up.  

        @returns: (newModulesDict, connectionList) - newModulesDict maps from
        serialised/OLD instance name to newly created instance; newConnections
        is a connectionList of the connections taht really were made during
        the deserialisation.

        @TODO: this should go to NetworkManager and should return meta_modules
        in the dictionary, not module instances.
        """

        # store and deactivate auto-execute
        ae = self.auto_execute
        self.auto_execute = False
        
        # newModulesDict will act as translator between pickled instance_name
        # and new instance!
        newModulesDict = {}
        failed_modules_dict = []
        for pmsTuple in pmsDict.items():
            # each pmsTuple == (instance_name, pms)
            # we're only going to try to create a module if the module_man
            # says it's available!
            try:
                newModule = self.create_module(pmsTuple[1].module_name)
                
            except ModuleManagerException, e:
                self._devide_app.log_error_with_exception(
                    'Could not create module %s:\n%s.' %
                    (pmsTuple[1].module_name, str(e)))
                # make sure
                newModule = None
                
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
                    configCopy = copy.deepcopy(pmsTuple[1].module_config)
                    # the API says we have to call get_config() first,
                    # so that the module has another place where it
                    # could lazy prepare the thing (slice3dVWR does
                    # this)
                    cfg = newModule.get_config()
                    # now we merge the stored config with the new
                    # module config
                    cfg.__dict__.update(configCopy.__dict__)
                    # and then we set it back with set_config
                    newModule.set_config(cfg)
                except Exception, e:
                    # it could be a module with no defined config logic
                    self._devide_app.log_warning(
                        'Could not restore state/config to module %s: %s' %
                        (newModule.__class__.__name__, e))
                
                # try to rename the module to the pickled unique instance name
                # if this name is already taken, use the generated unique instance
                # name
                self.rename_module(newModule,pmsTuple[1].instance_name)
                
                # and record that it's been recreated (once again keyed
                # on the OLD unique instance name)
                newModulesDict[pmsTuple[1].instance_name] = newModule

        # now we're going to connect all of the successfully created
        # modules together; we iterate DOWNWARDS through the different
        # consumerTypes
        
        newConnections = []
        for connection_type in range(max(self.consumerTypeTable.values()) + 1):
            typeConnections = [connection for connection in connectionList
                               if connection.connection_type == connection_type]
            
            for connection in typeConnections:
                if newModulesDict.has_key(connection.source_instance_name) and \
                   newModulesDict.has_key(connection.target_instance_name):
                    sourceM = newModulesDict[connection.source_instance_name]
                    targetM = newModulesDict[connection.target_instance_name]
                    # attempt connecting them
                    print "connecting %s:%d to %s:%d..." % \
                          (sourceM.__class__.__name__, connection.output_idx,
                           targetM.__class__.__name__, connection.input_idx)

                    try:
                        self.connect_modules(sourceM, connection.output_idx,
                                            targetM, connection.input_idx)
                    except:
                        pass
                    else:
                        newConnections.append(connection)

        # now do the POST connection module config!
        for oldInstanceName,newModuleInstance in newModulesDict.items():
            # retrieve the pickled module state
            pms = pmsDict[oldInstanceName]
            # take care to deep copy the config
            configCopy = copy.deepcopy(pms.module_config)

            # now try to call set_configPostConnect
            try:
                newModuleInstance.set_configPostConnect(configCopy)
            except AttributeError:
                pass
            except Exception, e:
                # it could be a module with no defined config logic
                self._devide_app.log_warning(
                    'Could not restore post connect state/config to module '
                    '%s: %s' % (newModuleInstance.__class__.__name__, e))
                
        # reset auto_execute
        self.auto_execute = ae

        # we return a dictionary, keyed on OLD pickled name with value
        # the newly created module-instance and a list with the connections
        return (newModulesDict, newConnections)

    def request_auto_execute_network(self, module_instance):
        """Method that can be called by an interaction/view module to
        indicate that some action by the user should result in a network
        update.  The execution will only be performed if the
        AutoExecute mode is active.
        """

        if self.auto_execute:
            print "auto_execute ##### #####"
            self.execute_network()

    def serialise_module_instances(self, module_instances):
        """Given 
        """

        # dictionary of pickled module instances keyed on unique module
        # instance name
        pmsDict = {}
        # we'll use this list internally to check later (during connection
        # pickling) which modules are being written away
        pickledModuleInstances = []
        
        for module_instance in module_instances:
            if self._module_dict.has_key(module_instance):

                # first get the MetaModule
                mModule = self._module_dict[module_instance]
                
                # create a picklable thingy
                pms = PickledModuleState()
                
                try:
                    print "SERIALISE: %s - %s" % \
                          (str(module_instance),
                           str(module_instance.get_config()))
                    pms.module_config = module_instance.get_config()
                except AttributeError, e:
                    self._devide_app.log_warning(
                        'Could not extract state (config) from module %s: %s' \
                        % (module_instance.__class__.__name__, str(e)))

                    # if we can't get a config, we pickle a default
                    pms.module_config = DefaultConfigClass()
                    
                #pms.module_name = module_instance.__class__.__name__
                # we need to store the complete module name
                # we could also get this from meta_module.module_name
                pms.module_name = module_instance.__class__.__module__

                # this will only be used for uniqueness purposes
                pms.instance_name = mModule.instance_name

                pmsDict[pms.instance_name] = pms
                pickledModuleInstances.append(module_instance)

        # now iterate through all the actually pickled module instances
        # and store all connections in a connections list
        # three different types of connections:
        # 0. connections with source modules with no inputs
        # 1. normal connections
        # 2. connections with targets that are exceptions, e.g. sliceViewer
        connectionList = []
        for module_instance in pickledModuleInstances:
            mModule = self._module_dict[module_instance]
            # we only have to iterate through all outputs
            for output_idx in range(len(mModule.outputs)):
                outputConnections = mModule.outputs[output_idx]
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
                            connection_type = self.consumerTypeTable[
                                moduleClassName]
                        else:
                            connection_type = 1
                            # FIXME: we still have to check for 0: iterate
                            # through all inputs, check that none of the
                            # supplier modules are in the list that we're
                            # going to pickle

                        print '%s has connection type %d' % \
                              (outputConnection[0].__class__.__name__,
                               connection_type)
                        
                        connection = PickledConnection(
                            mModule.instance_name, output_idx,
                            self._module_dict[outputConnection[0]].instance_name,
                            outputConnection[1],
                            connection_type)
                                                       
                        connectionList.append(connection)

        return (pmsDict, connectionList)

    def generic_progress_callback(self, progressObject,
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
    

    def get_consumers(self, meta_module):
        """Determine meta modules that are connected to the outputs of
        meta_module.

        This method is called by: scheduler, self.recreate_module_in_place.

        @todo: this should be part of the MetaModule code, as soon as
        the MetaModule inputs and outputs are of type MetaModule and not
        instance.

        @param instance: module instance of which the consumers should be
        determined.
        @return: list of tuples, each consisting of (this module's output
        index, the consumer meta module, the consumer input index)
        """

        consumers = []

        # get outputs from MetaModule: this is a list of list of tuples
        # outer list has number of outputs elements
        # inner lists store consumer modules for that output
        # tuple contains (consumerModuleInstance, consumerInputIdx)
        outputs = meta_module.outputs

        for output_idx in range(len(outputs)):
            output = outputs[output_idx]
            for consumerInstance, consumerInputIdx in output:
                consumerMetaModule = self._module_dict[consumerInstance]
                consumers.append(
                    (output_idx, consumerMetaModule, consumerInputIdx))

        return consumers

    def get_producers(self, meta_module):
        """Return a list of meta modules, output indices and the input
        index through which they supply 'meta_module' with data.

        @todo: this should be part of the MetaModule code, as soon as
        the MetaModule inputs and outputs are of type MetaModule and not
        instance.

        @param meta_module: consumer meta module.
        @return: list of tuples, each tuple consists of producer meta module
        and output index as well as input index of the instance input that
        they connect to.
        """
        
        # inputs is a list of tuples, each tuple containing module_instance
        # and output_idx of the producer/supplier module; if the port is
        # not connected, that position in inputs contains "None"
        inputs = meta_module.inputs

        producers = []
        for i in range(len(inputs)):
            pTuple = inputs[i]
            if pTuple is not None:
                # unpack
                pInstance, pOutputIdx = pTuple
                pMetaModule = self._module_dict[pInstance]
                # and store
                producers.append((pMetaModule, pOutputIdx, i))

        return producers

    def setModified_DEPRECATED(self, module_instance):
        """Changed modified ivar in MetaModule.

        This ivar is used to determine whether module_instance needs to be
        executed to become up to date.  It should be set whenever changes
        are made that dirty the module state, for example parameter changes
        or topology changes.

        @param module_instance: the instance whose modified state sbould be
        changed.
        @param value: the new value of the modified ivar, True or False.
        """
        
        self._module_dict[module_instance].modified = True 

    def set_progress(self, progress, message, noTime=False):
        """Progress is in percent.
        """
        self._devide_app.set_progress(progress, message, noTime)

    setProgress = set_progress

    def _make_unique_instance_name(self, instance_name=None):
        """Ensure that instance_name is unique or create a new unique
        instance_name.

        If instance_name is None, a unique one will be created.  An
        instance_name (whether created or passed) will be permuted until it
        unique and then returned.
        """
        
        # first we make sure we have a unique instance name
        if not instance_name:
            instance_name = "dvm%d" % (len(self._module_dict),)

        # now make sure that instance_name is unique
        uniqueName = False
        while not uniqueName:
            # first check that this doesn't exist in the module dictionary
            uniqueName = True
            for mmt in self._module_dict.items():
                if mmt[1].instance_name == instance_name:
                    uniqueName = False
                    break

            if not uniqueName:
                # this means that this exists already!
                # create a random 3 character string
                chars = 'abcdefghijklmnopqrstuvwxyz'

                tl = ""
                for i in range(3):
                    tl += choice(chars)
                        
                instance_name = "%s%s%d" % (instance_name, tl,
                                           len(self._module_dict))

        
        return instance_name

    def rename_module(self, instance, name):
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
        
        while (self.get_instance(name) != None):
            # add a number (%d) until the name is unique
            name = '%s (%d)' % (basename, i)
            i += 1

        try:
            # get the MetaModule and rename it.
            self._module_dict[instance].instance_name = name
        except Exception:
            return False

        # some modules and mixins support the rename call and use it
        # to change their window titles.  Neat.
        # this was added on 20090322, so it's not supported
        # everywhere.
        try:
            instance.rename(name)
        except AttributeError:
            pass

        # everything proceeded according to plan.        
        # so return the new name
        return name

    def modify_module(self, module_instance, part=0):
        """Call this whenever module state has changed in such a way that
        necessitates a re-execution, for instance when parameters have been
        changed or when new input data has been transferred.
        """

        self._module_dict[module_instance].modify(part)

    modify_module = modify_module

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
        prod_tuples = self.get_producers(meta_module)
        # cons_tuples contains a list of (output_index, consumer_meta_module,
        # consumer input index)
        cons_tuples = self.get_consumers(meta_module)
        # store the instance name
        instance_name = meta_module.instance_name
        # and the full module spec name
        full_name = meta_module.module_name
        # and get the module state (we make a deep copy just in case)
        module_config = copy.deepcopy(meta_module.instance.get_config())

        # 2. instantiate a new one and give it its old config
        ###############################################################
        # because we instantiate the new one first, if this instantiation
        # breaks, an exception will be raised and no harm will be done,
        # we still have the old one lying around

        # instantiate
        new_instance = self.create_module(full_name, instance_name)
        # and give it its old config back
        new_instance.set_config(module_config)

        # 3. delete the old module
        #############################################################
        self.delete_module(meta_module.instance)

        # 4. now rename the new module
        #############################################################

        # find the corresponding new meta_module
        meta_module = self._module_dict[new_instance]
        # give it its old name back
        meta_module.instance_name = instance_name

        # 5. connect it up
        #############################################################
        for producer_meta_module, output_idx, input_idx in prod_tuples:
            self.connect_modules(
                producer_meta_module.instance, output_idx,
                new_instance, input_idx)

        for output_idx, consumer_meta_module, input_idx in cons_tuples:
            self.connect_modules(
                new_instance, output_idx,
                consumer_meta_module.instance, input_idx)

        # we should be done now
        return meta_module
        

    def should_execute_module(self, meta_module, part=0):

        """Determine whether module_instance requires execution to become
        up to date.

        Execution is required when the module is new or when the user has made
        parameter or introspection changes.  All of these conditions should be
        indicated by calling L{ModuleManager.modify(instance)}.

        @return: True if execution required, False if not.
        """

        return meta_module.shouldExecute(part)

    def should_transfer_output(
        self,
        meta_module, output_idx, consumer_meta_module,
        consumer_input_idx, streaming=False):
        
        """Determine whether output data has to be transferred from
        module_instance via output outputIndex to module consumerInstance.

        Output needs to be transferred if:
         - module_instance has new or changed output (i.e. it has
           executed after the previous transfer)
         - consumerInstance does not have the data yet
        Both of these cases are handled with a transfer timestamp per
        output connection (defined by output idx, consumer module, and
        consumer input idx)

        This method is used by the scheduler.

        @return: True if output should be transferred, False if not.
        """
        
        return meta_module.should_transfer_output(
            output_idx, consumer_meta_module, consumer_input_idx,
            streaming)

        
    def transfer_output(
        self,
        meta_module, output_idx, consumer_meta_module,
        consumer_input_idx, streaming=False):

        """Transfer output data from module_instance to the consumer modules
        connected to its specified output indexes.

        This will be called by the scheduler right before execution to
        transfer the given output from module_instance instance to the correct
        input on the consumerInstance.  In general, this is only done if
        should_transfer_output is true, so the number of unnecessary transfers
        should be minimised.

        This method is in ModuleManager and not in MetaModule because it
        involves more than one MetaModule.

        @param module_instance: producer module whose output data must be
        transferred.
        @param outputIndex: only output data produced by this output will
        be transferred.
        @param consumerInstance: only data going to this instance will be
        transferred.
        @param consumerInputIdx: data enters consumerInstance via this input
        port.

        @raise ModuleManagerException: if an error occurs getting the data
        from or transferring it to a new module.
        """

        #print 'transferring data %s:%d' % (module_instance.__class__.__name__,
        #                                   outputIndex)

        # double check that this connection already exists

        consumer_instance = consumer_meta_module.instance
        if meta_module.findConsumerInOutputConnections(
            output_idx, consumer_instance, consumer_input_idx) == -1:

            raise Exception, 'ModuleManager.transfer_output called for ' \
                  'connection that does not exist.'
        
        try:
            # get data from producerModule output
            od = meta_module.instance.get_output(output_idx)

        except Exception, e:
            # get details about the errored module
            instance_name = meta_module.instance_name
            module_name = meta_module.instance.__class__.__name__

            # and raise the relevant exception
            es = 'Faulty transfer_output (get_output on module %s (%s)): %s' \
                 % (instance_name, module_name, str(e))
                 
            # we use the three argument form so that we can add a new
            # message to the exception but we get to see the old traceback
            # see: http://docs.python.org/ref/raise.html
            raise ModuleManagerException, es, sys.exc_info()[2]

        # we only disconnect if we're NOT streaming!
        if not streaming:
            # experiment here with making shallowcopies if we're working with
            # VTK data.  I've double-checked (20071027): calling update on
            # a shallowcopy is not able to get a VTK pipeline to execute.
            # TODO: somehow this should be part of one of the moduleKits
            # or some other module-related pluggable logic.
            if od and hasattr(od, 'GetClassName') and hasattr(od, 'ShallowCopy'):
                nod = od.__class__()
                nod.ShallowCopy(od)
                od = nod
            
        try:
            # set on consumerInstance input
            consumer_meta_module.instance.set_input(consumer_input_idx, od)

            
        except Exception, e:
            # get details about the errored module
            instance_name = consumer_meta_module.instance_name
            module_name = consumer_meta_module.instance.__class__.__name__

            # and raise the relevant exception
            es = 'Faulty transfer_output (set_input on module %s (%s)): %s' \
                 % (instance_name, module_name, str(e))

            # we use the three argument form so that we can add a new
            # message to the exception but we get to see the old traceback
            # see: http://docs.python.org/ref/raise.html
            raise ModuleManagerException, es, sys.exc_info()[2]
        

        # record that the transfer has just happened
        meta_module.timeStampTransferTime(
            output_idx, consumer_instance, consumer_input_idx,
            streaming)

        # also invalidate the consumerModule: it should re-execute when
        # a transfer has been made.  We only invalidate the part that
        # takes responsibility for that input.
        part = consumer_meta_module.getPartForInput(consumer_input_idx)
        consumer_meta_module.modify(part)

        #print "modified", consumer_meta_module.instance.__class__.__name__

        # execute on change
        # we probably shouldn't automatically execute here... transfers
        # mean that some sort of network execution is already running
