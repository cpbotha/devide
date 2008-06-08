# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

import sys

VERSION = 'INTEGRATED'

# debug print command: if DEBUG is true, outputs to stdout, if not
# then outputs nothing.
# import with: from module_kits.misc_kit import dprint
DEBUG=False
if DEBUG:
    def dprint(*msg):
        print msg
else:
    def dprint(*msg):
        pass


def init(module_manager):
    global misc_utils
    import misc_utils

    global types
    module_manager.set_progress(100, 'Initialising misc_kit: complete.')


