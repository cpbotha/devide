# updates all DeVIDE dependencies except ITK and VTK
# i.e. do a cvs update, a cmake and a build of:
# vtkdevide, vtktud
# TODO: ConnectVTKITK
# $Id$
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
# --- END updateAllDefaults
try:
    import updateAllDefaults as defaults
except ImportError, e:
    print 'Error loading updateAllDefaults.py: %s' % (str(e),)
    sys.exit()

# buildcommands for posix and MSVS 7.1 on Windows
if os.name == 'posix':
    buildCommand = 'make'
    svn_update_command = 'svn update'
    cmake_update_command = 'cmake .'
else:
    # first %s is to be replaced by the .sln file
    buildCommand = 'devenv %s /project ALL_BUILD /projectconfig ' \
                   '"RelWithDebInfo|Win32" /build RelWithDebInfo'
    svn_update_command = 'c:/apps/subversion/bin/svn update'
    cmake_update_command = '"c:\\program files\\cmake 2.4\\bin\\cmake" .'

def standardUpdate(source):
    print '\nSVN updating %s\n' % (source,)
    os.chdir(source)
    os.system(svn_update_command)

def standardBuild(binary, slnFile):
    print '\nUpdating build config in %s' % (binary,)
    os.chdir(binary)
    os.system(cmake_update_command)

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
        #standardUpdate(defaults.wrapitkSource)
        pass

def doBuilds(itkRequested):
    standardBuild(defaults.vtkdevideBinary, 'vtkdevide.sln')
    standardBuild(defaults.vtktudBinary, 'vtktud.sln')
    if itkRequested:
        #standardBuild(defaults.wrapitkBinary, 'wrapitk.sln')
        pass

def dispUsage():
    print "-h or --help               : Display this message."
    print "--noUpdates                : Do not do any SVN updates."
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

        elif o in ('--noUpdates',):
            updatesRequested = False
            
        elif o in ('--noBuilds',):
            buildsRequested = False

        elif o in ('--noItk', '--no-itk'):
            itkRequested = False

    if updatesRequested:
        doUpdates(itkRequested)

    if buildsRequested:
        doBuilds(itkRequested)

if __name__ == '__main__':
    main()

