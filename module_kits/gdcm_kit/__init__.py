# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.


"""gdcm_kit driver module.

This pre-loads GDCM2, the second generation Grass Roots Dicom library,
used since 2008 by DeVIDE for improved DICOM loading / saving support.
"""

import os
import sys

VERSION = ''

def init(module_manager):
    # as of 20080628, the order of importing vtkgdcm and gdcm IS
    # important on Linux.  vtkgdcm needs to go before gdcm, else very
    # strange things happen due to the dl (dynamic loading) switches.
    global vtkgdcm
    import vtkgdcm

    # gdcm post 2.0.8 will have a new scheme for locating Part3.xml:

    # 2. Or directly from your application / python code, simply
    # Append/Prepend your exotic path:

    # Example in python:

    #  import gdcm
    #  g=gdcm.Global.GetInstance()
    #  g.Prepend( my_exotic_path )
    #  g.LoadResourcesFiles()

    # -> should return True when set properly
    # -------------------------


    global gdcm
    import gdcm

    # will be available as module_kits.gdcm_kit.utils after the client
    # programmer has done module_kits.gdcm_kit
    import module_kits.gdcm_kit.utils

    global VERSION
    VERSION = gdcm.Version.GetVersion()


    module_manager.set_progress(100, 'Initialising gdcm_kit: complete.')

