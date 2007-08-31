# updates all DeVIDE dependencies except ITK and VTK
# i.e. do a svn update, a cmake and a build of:
# vtkdevide, vtktud, itktud (build and install)
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
# itktudSource = 'c:/work/code/itktud'
# itktudBinary = 'c:/build/itktud'
# --- END updateAllDefaults
try:
    import updateAllDefaults as defaults
except ImportError, e:
    print 'Error loading updateAllDefaults.py: %s' % (str(e),)
    sys.exit()

# buildcommands for posix and MSVS 8 (2005) on Windows
if os.name == 'posix':
    buildCommand = 'make'
    install_command = 'make install'
    svn_update_command = 'svn update'
    cmake_update_command = 'cmake .'
else:
    # first %s is to be replaced by the .sln file
    buildCommand = 'devenv %s /project ALL_BUILD /projectconfig ' \
                   '"RelWithDebInfo|Win32" /build RelWithDebInfo'
    install_command = 'devenv %s /project INSTALL /projectconfig ' \
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

def standard_install(binary, sln_file):
    print '\nInstalling from %s' % (binary,)
    os.chdir(binary)

    if os.name == 'posix':
        the_install_command = install_command
    else:
        the_install_command = install_command % (sln_file,)

    print 'Installing with "%s"\n' % (the_install_command,)

    os.system(the_install_command)

def doUpdates():
    standardUpdate(defaults.devideTopLevel)
    standardUpdate(defaults.vtkdevideSource)
    standardUpdate(defaults.vtktudSource)
    standardUpdate(defaults.itktudSource)

def doBuilds():
    standardBuild(defaults.vtkdevideBinary, 'vtkdevide.sln')
    standardBuild(defaults.vtktudBinary, 'vtktud.sln')
    standardBuild(defaults.itktudBinary, 'itktud.sln')

def do_installs():
    standard_install(defaults.itktudBinary, 'itktud.sln')

def dispUsage():
    print "-h or --help               : Display this message."
    print "--noUpdates                : Do not do any SVN updates."
    print "--noBuilds                 : Do not do any builds."
    print "--no_installs              : Do not do any installs."

def main():
    updatesRequested = True
    buildsRequested = True
    installs_requested = True
    
    try:
        # 'p:' means -p with something after
        optlist, args = getopt.getopt(
            sys.argv[1:], 'h',
            ['help', 'noUpdates', 'noBuilds', 'no_installs'])

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

        elif o in ('--no_installs',):
            installs_requested = False
            

    if updatesRequested:
        doUpdates()

    if buildsRequested:
        doBuilds()

    if installs_requested:
        do_installs()

if __name__ == '__main__':
    main()

