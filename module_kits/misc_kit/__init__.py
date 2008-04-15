# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

import sys

VERSION = 'INTEGRATED'

def init(module_manager):
    global misc_utils
    import misc_utils
    # make sure misc_utils is available everywhere
    sys.modules['misc_utils'] = misc_utils
    module_manager.set_progress(100, 'Initialising misc_kit: complete.')


