# updates all DeVIDE dependencies except ITK and VTK
# i.e. do a cvs update, a cmake and a build of:
# vtkdevide, vtktud, wrapitk and, depending on ITK: wrapitk, ConnectVTKITK
# $Id: updateAll.py,v 1.3 2005/01/11 22:42:06 cpbotha Exp $
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

def standardUpdate(source):
    print '\nCVS updating %s\n' % (source,)
    os.chdir(source)
    os.system(cvsUpdateCommand)

def standardBuild(binary, slnFile):
    print '\nUpdating build config in %s' % (binary,)
    os.chdir(binary)
    os.system('cmake .')

    if os.name == 'posix':
        theBuildCommand = buildCommand
    else:
        theBuildCommand = buildCommand % (slnFile,)

    print 'Building with "%s"\n' % (theBuildCommand,)

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

def doUpdates():
    standardUpdate(defaults.devideTopLevel)
    standardUpdate(defaults.vtkdevideSource)
    standardUpdate(defaults.vtktudSource)
    standardUpdate(defaults.wrapitkSource)

def doBuilds():
    standardBuild(defaults.vtkdevideBinary, 'vtkdevide.sln')
    standardBuild(defaults.vtktudBinary, 'vtutud.sln')
    standardBuild(defaults.wrapitkBinary, 'wrapitk.sln')

def main():
    doUpdates()
    doBuilds()

if __name__ == '__main__':
    main()

