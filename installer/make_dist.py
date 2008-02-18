# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

import getopt
import os
import shutil
import sys

PPF = "[*** DeVIDE make_dist ***]"

class MDPaths:
    """Initialise all directories required for building DeVIDE
    distributables.
    """
    def __init__(self, specfile, pyinstaller_script):
        self.specfile = os.path.normpath(specfile)
        self.pyinstaller_script = os.path.normpath(pyinstaller_script)

        # devide/installer
        self.specfile_dir = os.path.normpath(
                os.path.dirname(self.specfile))

        self.pyi_dist_dir = os.path.join(self.specfile_dir,
                'distdevide')
        self.pyi_build_dir = os.path.join(self.specfile_dir,
                'builddevide')

        # devide
        self.devide_dir = \
            os.path.normpath(
                    os.path.join(self.specfile_dir, '..'))
        

def usage():
    message = """
make_dist.py - build DeVIDE distributables.

Invoke as follows:
python make_dist.py -s specfile -i installer_script
where specfile is the pyinstaller spec file and installer_script
refers to the full path of the pyinstaller Build.py 

The specfile should be in the directory devide/installer, where devide
contains the devide source that you are using to build the
distributables.
"""

    print message

def clean_pyinstaller(md_paths):
    """Clean out pyinstaller dist and build directories so that it has
    to do everything from scratch.  We usually do this before building
    full release versions.
    """
    
    if os.path.isdir(md_paths.pyi_dist_dir):
        print PPF, "Removing distdevide..."
        shutil.rmtree(md_paths.pyi_dist_dir)

    if os.path.isdir(md_paths.pyi_build_dir):
        print PPF, "Removing builddevide..."
        shutil.rmtree(md_paths.pyi_build_dir)

def run_pyinstaller(md_paths):
    """Run pyinstaller with the given parameters.  This does not clean
    out the dist and build directories before it begins
    """

    # old makePackage.sh would remove all *.pyc, *~ and #*# files
    cmd = '%s %s %s' % (sys.executable, md_paths.pyinstaller_script,
            md_paths.specfile)
    
    ret = os.system(cmd)

    if ret != 0:
       raise RuntimeError('Error running PYINSTALLER.') 

    if os.name == 'nt':
        for efile in ['devide.exe.manifest', 
                'msvcm80.dll', 'Microsoft.VC80.CRT.manifest']:
            print PPF, "WINDOWS: copying", efile
        
            src = os.path.join(
                md_paths.specfile_dir,
                efile)
            dst = os.path.join(
                md_paths.pyi_dist_dir,
                efile)

            shutil.copyfile(src, dst)

    else:
        # TODO FIXME TODO FIXME!

        # strip all libraries
        # find distdevide/ -name *.so | xargs strip

        # remove rpath information
        # find distdevide -name *.so | xargs chrpath --delete

        # rename binary and create invoking script
        # we only have to set LD_LIBRARY_PATH, PYTHONPATH is correct
        # mv distdevide/devide distdevide/devide.bin
        # SCRIPTFILE='distdevide/devide'
        # cp devideInvokingScript.sh $SCRIPTFILE
        # chmod +x $SCRIPTFILE

        pass
   

def package_dist():
    """After pyinstaller has been executed, do all actions to package
    up a distribution.

    1. rebase all DLLs
    2. posix: strip and chrpath all SOs
    3. create WrapITK package
    4. package and timestamp distributables (nsis on win, tar on
    posix)
    """

    # recursively find all DLLs and PYDs
    for dirpath, dirnames, filenames in os.walk('.'):
        for fn in filenames:
            if fnmatch.fnmatch(fn, '*.pyd') or fnmatch.fnmatch(fn, '*.dll'):
                print fn

def main():
    try:
        optlist, args = getopt.getopt(
                sys.argv[1:], 'hs:i:',
                ['help', 'spec=','pyinstaller-script='])

    except getopt.GetoptError,e:
        usage
        return

    spec = None
    pyi_script = None

    for o, a in optlist:
        if o in ('-h', '--help'):
            usage()
            return

        elif o in ('-s', '--spec'):
            spec = a

        elif o in ('-i', '--pyinstaller-script'):
            pyi_script = a

    if spec is None or pyi_script is None:
        # we need BOTH the specfile and pyinstaller script
        usage()
        return

    md_paths = MDPaths(spec, pyi_script)

    clean_pyinstaller(md_paths)
    run_pyinstaller(md_paths)


if __name__ == '__main__':
    main()

