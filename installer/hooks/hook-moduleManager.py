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

# if sys.platform.startswith('win'):
#     sys.path.insert(0, 'g:/work/code/devide/')
# else:
#     sys.path.insert(0, '/home/cpbotha/work/code/devide/')

import modules

# * we need to give the module paths relative to the directory moduleManager
#   is in (I think, since this is the hook for moduleManager)
# * the installer will treat these imports as if they were explicitly
#   imported by the moduleManager, so THEIR dependecies will automatically
#   be analysed.
# * we have to look at the USE_INSIGHT defaults flag as well...
import defaults
ml2 = ["modules." + i for i in modules.moduleList if defaults.USE_INSIGHT or
       not i.startswith('Insight')]
hiddenimports = ml2

print "[*] hook-moduleManager.py - HIDDENIMPORTS"
print hiddenimports
