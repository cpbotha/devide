# $Id: __init__.py 1945 2006-03-05 01:06:37Z cpbotha $

# importing this module shouldn't directly cause other large imports
# do large imports in the init() hook so that you can call back to the
# ModuleManager progress handler methods.

"""stats_kit package driver file.

Inserts the following modules in sys.modules: stats.

@author: Charl P. Botha <http://cpbotha.net/>
"""

import sys

# you have to define this
VERSION = 'Strangman - May 10, 2002'

def init(theModuleManager):
    # import the main module itself
    global stats
    import stats
    # if we don't do this, the module will be in sys.modules as
    # module_kits.stats_kit.stats because it's not in the sys.path.
    # iow. if a module is in sys.path, "import module" will put 'module' in
    # sys.modules.  if a module isn't, "import module" will put
    # 'relative.path.to.module' in sys.path.
    sys.modules['stats'] = stats

    theModuleManager.setProgress(100, 'Initialising stats_kit: complete.')

def refresh():
    reload(stats)

    
