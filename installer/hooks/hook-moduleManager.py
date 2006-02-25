import os
import sys

# normalize path of this file, get dirname
hookDir = os.path.dirname(os.path.normpath(__file__))
# split dirname, select everything except the ending "installer/hooks"
dd = hookDir.split(os.sep)[0:-2]
# we have to do this trick, since on windows os.path.join('c:', 'blaat')
# yields 'c:blaat', i.e. relative to current dir, and we know it's absolute
dd[0] = '%s%s' % (dd[0], os.sep)
# turn that into a path again by making use of join (the normpath will take
# care of redundant slashes on *ix due to the above windows trick)
devideDir = os.path.normpath(os.path.join(*dd))

# now we've inserted the devideDir into the module path, so
# import modules should work
sys.path.insert(0, devideDir)

import module_kits
import defaults

# get a list of module kits
mkl = module_kits.module_kit_list[:]
# remove the no_kits
mkl = [i for i in mkl if i not in defaults.NOKITS]

hiddenimports = ['module_kits.%s' % (i,) for i in mkl]

print "[*] hook-moduleManager.py - HIDDENIMPORTS"
print hiddenimports

