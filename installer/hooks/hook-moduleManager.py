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

# now also parse config file
import ConfigParser
config_defaults = {'nokits': ''}
cp = ConfigParser.ConfigParser(config_defaults)
cp.read(os.path.join(devideDir, 'devide.cfg'))
nokits = [i.strip() for i in cp.get('DEFAULT', 'nokits').split(',')]

# get a list of module kits
mkl = module_kits.module_kit_list[:] + ['numpy_kit']
# 1. remove the no_kits
# 2. explicitly remove itk_kit, it's handled completely separately by
# the makePackage.sh script file
mkl = [i for i in mkl if i not in nokits and i not in
        ['itk_kit','itktudoss_kit']]

# other imports
other_imports = ['genMixins', 'genUtils', 'ModuleBase', 'moduleMixins',
                 'module_utils',
                 'modules.viewers.DICOMBrowser',
                 'modules.viewers.slice3dVWR',
                 'modules.viewers.histogram1D',
                 'modules.viewers.TFEditor']
# slice3dVWR is temporary, just to see if we can get it going this way.

hiddenimports = ['module_kits.%s' % (i,) for i in mkl] + other_imports

print "[*] hook-ModuleManager.py - HIDDENIMPORTS"
print hiddenimports

