# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

import sys

VERSION = ''

def init(module_manager):
    global gdcm
    import gdcm

    global vtkgdcm
    import vtkgdcm

    global VERSION
    VERSION = gdcm.Version.GetVersion()
