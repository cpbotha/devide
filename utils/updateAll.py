# updates all DeVIDE dependencies except ITK and VTK
# i.e. do a cvs update, a cmake and a build of:
# vtkdevide, vtktud, wrapitk and, depending on ITK: wrapitk, ConnectVTKITK
# $Id: updateAll.py,v 1.2 2005/01/06 21:09:36 cpbotha Exp $
# authored by Charl P. Botha http://cpbotha.net/

import os
import sys

# There should be an updateAllDefaults.py file in the same directory
# as this script.  An example would be:
# --- BEGIN updateAllDefaults.py
# devideTopLevel = '/home/cpbotha/work/code/devide'
# vtkdevideSource = '/home/cpbotha/work/code/vtkdevide'
# vtkdevideBinary = '/home/cpbotha/work/code/vtkdevide'
# vtktudSource = '/home/cpbotha/work/code/vtktud'
# vtktudBinary = '/home/cpbotha/work/code/vtktud'
# wrapitkSource = '/home/cpbotha/work/code/wrapitk'
# wrapitkBinary = '/home/cpbotha/work/code/wrapitk-gcc'
# --- END updateAllDefaults
try:
    import updateAllDefaults as defaults
except ImportError, e:
    print 'Error loading updateAllDefaults.py: %s' % (str(e),)
    sys.exit()

# buildcommands for posix and MSVS 7.1 on Windows
if os.name == 'posix':
    buildCommand = 'make'
else:
    # first %s is to be replaced by the .sln file
    buildCommand = 'devenv %s /project ALL_BUILD /projectconfig ' \
                   '"RelWithDebInfo|Win32" /build RelWithDebInfo'

cvsUpdateCommand = 'cvs -z3 update -dAP'

def updatedevide():
    print 'CVS updating %s' % (defaults.devideTopLevel,)
    os.chdir(defaults.devideTopLevel)
    os.system(cvsUpdateCommand)

def standardUpdateAndBuild(source, binary, slnFile):
    print 'CVS updating %s' % (source,)
    os.chdir(source)
    os.system(cvsUpdateCommand)

    print 'Updating build config in %s' % (binary,)
    os.chdir(binary)
    os.system('cmake .')


    if os.name == 'posix':
        theBuildCommand = buildCommand
    else:
        theBuildCommand = buildCommand % (slnFile,)

    print 'Building with "%s"' % (theBuildCommand,)

    os.system(theBuildCommand)
    

def updatevtkdevide():
    standardUpdateAndBuild(defaults.vtkdevideSource, defaults.vtkdevideBinary,
                           'vtkdevide.sln')

def updatevtktud():
    standardUpdateAndBuild(defaults.vtktudSource, defaults.vtktudBinary,
                           'vtktud.sln')
    
def updatewrapitk():
    standardUpdateAndBuild(defaults.wrapitkSource, defaults.wrapitkBinary,
                           'wrapitk.sln')

def main():
    updatedevide()
    updatevtkdevide()
    updatevtktud()
    updatewrapitk()

if __name__ == '__main__':
    main()

