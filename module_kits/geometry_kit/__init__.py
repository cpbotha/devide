# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

# importing this module shouldn't directly cause other large imports
# do large imports in the init() hook so that you can call back to the
# moduleManager progress handler methods.

"""geometry_kit package driver file.

Inserts the following modules in sys.modules: geometry.

@author: Charl P. Botha <http://cpbotha.net/>
"""

import sys

# you have to define this
VERSION = 'INTEGRATED'

def init(module_manager):
    global geometry
    import geometry

    # if we don't do this, the module will be in sys.modules as
    # module_kits.stats_kit.stats because it's not in the sys.path.
    # iow. if a module is in sys.path, "import module" will put 'module' in
    # sys.modules.  if a module isn't, "import module" will put
    # 'relative.path.to.module' in sys.path.
    sys.modules['geometry'] = geometry
    
    module_manager.set_progress(100, 'Initialising geometry_kit: complete.')

def refresh():
    # we have none of our own packages yet...
    global geometry
    reload(geometry)


    
