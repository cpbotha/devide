# updates all DeVIDE dependencies except ITK and VTK
# i.e. do a cvs update, a cmake and a build of:
# vtkdevide, vtktud, wrapitk and, depending on ITK: wrapitk, ConnectVTKITK
# $Id: updateAll.py,v 1.1 2005/01/06 18:27:52 cpbotha Exp $
# authored by Charl P. Botha http://cpbotha.net/

import os
import sys

# relative paths for all these thingies
# need source and bin dirs!
devideTopLevel = '../'
vtkdevideTopLevel = '../../vtkdevide/'
vtktudTopLevel = '../../vtktud/'
wrapitkTopLevel = '../../wrapitk-gcc/'

# buildcommand
if os.name == 'posix':
    buildCommand = 'make'
else:
    buildCommand = './msBuild.bat'

def updatedevide(ourpath):
    print 'DEVIDE ---'
    print 'CVS updating'
    os.chdir(os.path.join(ourpath, devideTopLevel))
    os.system('cvs update -dAP')

def updatevtkdevide(ourpath):
    print 'VTKDEVIDE ---'

    print 'CVS updating'
    os.chdir(os.path.join(ourpath, vtkdevideTopLevel))
    os.system('cvs update -dAP')

    print 'Configuring build'
    os.system('cmake .')

    print 'Building'
    os.system(buildCommand)

def updatevtktud(ourpath):
    print 'VTKTUD ---'

    print 'CVS updating'
    os.chdir(os.path.join(ourpath, vtktudTopLevel))
    os.system('cvs update -dAP')

    print 'Configuring build'
    os.system('cmake .')

    print 'Building'
    os.system(buildCommand)

def updatewrapitk(ourpath):
    print 'WRAPITK ---'

    print 'CVS updating'
    os.chdir(os.path.join(ourpath, wrapitkTopLevel))
    os.system('cvs update -dAP')

    print 'Configuring build'
    os.system('cmake .')

    print 'Building'
    os.system(buildCommand)
    
    

def main():
    # get our canonical path
    ourpath = os.path.abspath(os.path.dirname(sys.argv[0]))
    print 'ourpath == %s' % (ourpath,)

    updatedevide(ourpath)
    updatevtkdevide(ourpath)
    updatevtktud(ourpath)
    updatewrapitk(ourpath)


if __name__ == '__main__':
    main()

