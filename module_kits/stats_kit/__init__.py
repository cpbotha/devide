# $Id: __init__.py 1945 2006-03-05 01:06:37Z cpbotha $

# importing this module shouldn't directly cause other large imports
# do large imports in the init() hook so that you can call back to the
# moduleManager progress handler methods.

"""stats_kit package driver file.

Inserts the following modules in sys.modules: stats.

@author: Charl P. Botha <http://cpbotha.net/>
"""

# you have to define this
VERSION = 'Strangman - May 10, 2002'

def init(theModuleManager):
    # import the main module itself
    global stats
    import stats

    theModuleManager.setProgress(100, 'Initialising stats_kit: complete.')
