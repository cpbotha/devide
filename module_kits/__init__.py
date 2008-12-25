# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

import ConfigParser
import glob
import os
import sys


"""Top-level __init__ of the module_kits.

@ivar module_kits_list: All moduleKits in this list will have their init()s
called with the ModuleManager as parameter (after being imported).  Before
this happens though, members of this list that are also in the no-kits list
(defined by defaults.py or command-line) will be removed.  The kits will be
imported in the order that they are specified.  Make sure that kits dependent
on other kits occur after those kits in the list, the dependency checker is
that simple.  After all kit loading is complete, the module_kit_list will
contain the names of the kits that were successfully loaded.

@ivar crucial_kits: Usually, when a kit raises an exception during its init()
call, this is ignored and DeVIDE starts up as usual.  However, if the module
is in the crucial_kit_list, DeVIDE will refuse to start up.
"""

module_kit_list = []

module_kit_list2 = ['sqlite_kit', 'wx_kit', 'vtk_kit', 'vtktudoss_kit',
                   'gdcm_kit',
                   'itk_kit', 'itktudoss_kit',
                   'numpy_kit', 'matplotlib_kit', 'stats_kit',
                   'geometry_kit', 'misc_kit']

dependencies_dict2 = {'vtktudoss_kit' : ['vtk_kit'],
                     'gdcm_kit' : ['vtk_kit'],
                     'matplotlib_kit' : ['numpy_kit'],
                     'itktudoss_kit' : ['itk_kit'],
                     'geometry_kit' : ['numpy_kit']}

crucial_kit_list2 = ['wx_kit', 'vtk_kit']

class MKDef:
    def __init__(self):
        self.name = ''
        self.crucial = False
        self.priority = 100
        self.dependencies = []


def load(module_manager):

    module_kits_dir = os.path.join(
            module_manager.get_appdir(), 'module_kits')
    mkd_fnames = glob.glob(
            os.path.join(module_kits_dir, '*.mkd'))

    mkd_defaults = {
            'crucial' : False,
            'priority' : 100,
            'dependencies' : '' 
            }

    mkds = []

    for mkd_fname in mkd_fnames:
        mkd = MKDef()
        cp = ConfigParser.ConfigParser(mkd_defaults)
        cp.read(mkd_fname)
        mkd.name = os.path.splitext(os.path.basename(mkd_fname))[0]
        mkd.crucial = cp.getboolean('default', 'crucial')
        mkd.priority = cp.getint('default', 'priority')
        mkd.dependencies = [i.strip() 
                for i in cp.get('default', 'dependencies').split(',')
                if i]
        mkds.append(mkd)

    # now sort the mkds according to priority
    def cmp(a,b):
        if a.priority < b.priority:
            return -1
        elif a.priority > b.priority:
            return 1
        else:
            return 0

    mkds.sort(cmp)
    print [i.priority for i in mkds]

    # then remove the nokits
    nokits = module_manager.get_app_main_config().nokits
    mkds = [mkd for mkd in mkds
            if mkd.name not in nokits]

    loaded_kit_names = []

    # load the remaining kits
    for mkd in mkds:
        # first check that all dependencies are satisfied
        deps_satisfied = True
        for d in mkd.dependencies:
            if d not in loaded_kit_names:
                deps_satisfied = False
                # break out of the for loop
                break
                
        if not deps_satisfied:
            # skip this iteration of the for, go to the next iteration
            # (we don't want to try loading this module)
            continue
        
        try:
            # import module_kit into module_kits namespace
            exec('import module_kits.%s' % (mkd.name,))
            # call module_kit.init()
            getattr(module_kits, mkd.name).init(module_manager)
            # add it to the loaded_kits for dependency checking
            loaded_kit_names.append(mkd.name)

        except Exception, e:
            # if it's a crucial module_kit, we re-raise with our own
            # message added using th three argument raise form
            # see: http://docs.python.org/ref/raise.html
            if mkd.crucial:
                es = 'Error loading required module_kit %s: %s.' \
                     % (mkd.name, str(e))
                raise Exception, es, sys.exc_info()[2]
            
            
            # if not we can report the error and continue
            else:
                module_manager.log_error_with_exception(
                    'Unable to load non-critical module_kit %s: '
                    '%s.  Continuing with startup.' %
                    (mkd.name, str(e)))

        # if we got this far, startup was successful, but not all kits
        # were loaded: some not due to failure, and some not due to
        # unsatisfied dependencies.  set the current list to the list of
        # module_kits that did actually load.
        global module_kit_list
        module_kit_list = loaded_kit_names
       
   



