#import os
#import fnmatch
import sys

#mod_dir = os.path.join('/home/cpbotha/work/code/dscas3', 'modules')
#mods = ['modules.' + i
#        for i in os.listdir(mod_dir) if fnmatch.fnmatch(i, '*.py')]

sys.path.insert(0, '/home/cpbotha/work/code/dscas3/')
import modules

hiddenimports = ['module_base', 'module_constants', 'module_utils', \
                 'vtkcpbothapython', 'operator'] #+ modules.module_list
print hiddenimports

