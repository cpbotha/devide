# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

import sys

VERSION = 'INTEGRATED'

def init(module_manager):
    global misc_utils
    import misc_utils

    global types
    module_manager.set_progress(100, 'Initialising misc_kit: complete.')


