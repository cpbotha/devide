import os
import sys

sys.path.insert(0, '/home/cpbotha/work/code/dscas3/')
import modules

# * we need to give the module paths relative to the directory module_manager
#   is in (I think, since this is the hook for module_manager)
# * the installer will treat these imports as if they were explicitly
#   imported by the module_manager, so THEIR dependecies will automatically
#   be analysed.
ml2 = ["modules." + i for i in modules.module_list]
hiddenimports = ml2

print hiddenimports
