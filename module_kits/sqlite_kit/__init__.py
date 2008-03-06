# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

"""sqlite_kit package driver file.

With this we make sure that sqlite3 is always packaged.
"""

VERSION = ''

def init(module_manager):
    global sqlite3
    import sqlite3

    global VERSION
    VERSION = '%s (sqlite %s)' % (sqlite3.version,
            sqlite3.sqlite_version)

