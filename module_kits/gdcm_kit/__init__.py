# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.


"""gdcm_kit driver module.

This pre-loads GDCM2, the second generation Grass Roots Dicom library,
used since 2008 by DeVIDE for improved DICOM loading / saving support.
"""

import sys

VERSION = ''

def init(module_manager):
    global gdcm
    import gdcm

    global vtkgdcm
    import vtkgdcm

    # will be available as module_kits.gdcm_kit.utils after the client
    # programmer has done module_kits.gdcm_kit
    import module_kits.gdcm_kit.utils

    global VERSION
    VERSION = gdcm.Version.GetVersion()


    module_manager.set_progress(100, 'Initialising gdcm_kit: complete.')

