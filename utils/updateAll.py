# updates all DeVIDE dependencies except ITK and VTK
# i.e. do a cvs update, a cmake and a build of:
# vtkdevide, vtktud, wrapitk and, depending on ITK: wrapitk, ConnectVTKITK
# $Id: updateAll.py,v 1.5 2005/01/12 22:32:34 cpbotha Exp $
# authored by Charl P. Botha http://cpbotha.net/

import getopt
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
    

def doUpdates(itkRequested):
    standardUpdate(defaults.devideTopLevel)
    standardUpdate(defaults.vtkdevideSource)
    standardUpdate(defaults.vtktudSource)
    if itkRequested:
        standardUpdate(defaults.wrapitkSource)

def doBuilds():
    standardBuild(defaults.vtkdevideBinary, 'vtkdevide.sln')
    standardBuild(defaults.vtktudBinary, 'vtktud.sln')
    if itkRequested:
        standardBuild(defaults.wrapitkBinary, 'wrapitk.sln')

def dispUsage():
    print "-h or --help               : Display this message."
    print "--noUpdates                : Do not do any CVS updates."
    print "--noBuilds                 : Do not do any builds."
    print "--noItk or --no-itk        : Do not build any itk-related source."

def main():
    updatesRequested = True
    buildsRequested = True
    itkRequested = True
    
    try:
        # 'p:' means -p with something after
        optlist, args = getopt.getopt(
            sys.argv[1:], 'h',
            ['help', 'noUpdates', 'noBuilds', 'noItk', 'no-itk'])

    except getopt.GetoptError,e:
        dispUsage()
        sys.exit(1)

    for o, a in optlist:
        if o in ('-h', '--help'):
            dispUsage()
            sys.exit(1)

        elif o in ('--noUpdates'):
            updatesRequested = False
            
        elif o in ('--noBuilds'):
            buildsRequested = False

        elif o in ('--noItk', '--no-itk'):
            itkRequested = False

    if updatesRequested:
        doUpdates(itkRequested)

    if buildsRequested:
        doBuilds(itkRequested)

if __name__ == '__main__':
    main()

