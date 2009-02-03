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

def init(module_manager, pre_import=True):
    # as of 20080628, the order of importing vtkgdcm and gdcm IS
    # important on Linux.  vtkgdcm needs to go before gdcm, else very
    # strange things happen due to the dl (dynamic loading) switches.
    global vtkgdcm
    import vtkgdcm


    global gdcm
    import gdcm

    # since 2.0.9, we do the following to locate part3.xml:
    if hasattr(sys, 'frozen') and sys.frozen:
        g = gdcm.Global.GetInstance()
        # devide.spec puts Part3.xml in devide_dir/gdcmdata/XML/
        g.Prepend(os.path.join(
            module_manager.get_appdir(), 'gdcmdata','XML'))

        if not g.LoadResourcesFiles():
            raise RuntimeError('Could not setup GDCM resource files.')


    # will be available as module_kits.gdcm_kit.utils after the client
    # programmer has done module_kits.gdcm_kit
    import module_kits.gdcm_kit.utils

    global VERSION
    VERSION = gdcm.Version.GetVersion()


    module_manager.set_progress(100, 'Initialising gdcm_kit: complete.')

