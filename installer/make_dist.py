# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

import getopt
import os
import re
import shutil
import sys

PPF = "[*** DeVIDE make_dist ***]"


####################################################################
class MDPaths:
    """Initialise all directories required for building DeVIDE
    distributables.
    """
    def __init__(self, specfile, pyinstaller_script):
        self.specfile = os.path.normpath(specfile)
        self.pyinstaller_script = os.path.normpath(pyinstaller_script)

        # devide/installer
        self.specfile_dir = os.path.normpath(
                os.path.abspath(os.path.dirname(self.specfile)))

        self.pyi_dist_dir = os.path.join(self.specfile_dir,
                'distdevide')
        self.pyi_build_dir = os.path.join(self.specfile_dir,
                'builddevide')

        # devide
        self.devide_dir = \
            os.path.normpath(
                    os.path.join(self.specfile_dir, '..'))


####################################################################
# UTILITY METHODS
####################################################################
def get_status_output(command):
    """Run command, return output of command and exit code in status.
    In general, status is None for success and 1 for command not
    found.

    Method taken from johannes.utils.
    """

    ph = os.popen(command)
    output = ph.read()
    status = ph.close()
    return (status, output)


def find_command_with_ver(name, command, ver_re):
    """Try to run command, use ver_re regular expression to parse for
    the version string.  This will print for example:
    CVS: version 2.11 found.

    @return: True if command found, False if not or if version could
    not be parsed. 

    Method taken from johannes.utils.
    """

    retval = False
    s,o = get_status_output(command)

    if s:
        msg2 = 'NOT FOUND!'

    else:
        mo = re.search(ver_re, o, re.MULTILINE) 
        if mo:
            msg2 = 'version %s found.' % (mo.groups()[0],)
            retval = True
        else:
            msg2 = 'could not extract version.'


    print PPF, "%s: %s" % (name, msg2)

    return retval

def find_files(start_dir, re_pattern='.*\.(pyd|dll)'):
    """Recursively find all files (not directories) with filenames 
    matching given regular expression.  Case is ignored.

    @param start_dir: search starts in this directory
    @param re_pattern: regular expression with which all found files
    will be matched. example: re_pattern = '.*\.(pyd|dll)' will match
    all filenames ending in pyd or dll.
    @return: list of fully qualified filenames that satisfy the
    pattern
    """

    cpat = re.compile(re_pattern, re.IGNORECASE)
    found_files = []

    for dirpath, dirnames, filenames in os.walk(start_dir):
        ndirpath = os.path.normpath(os.path.abspath(dirpath))
        for fn in filenames:
            if cpat.match(fn):
                found_files.append(os.path.join(ndirpath,fn))

    return found_files

####################################################################
# METHODS CALLED FROM MAIN()
####################################################################
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

  

def package_dist(md_paths):
    """After pyinstaller has been executed, do all actions to package
    up a distribution.

    1. rebase all DLLs
    2. posix: strip and chrpath all SOs
    3. create WrapITK package
    4. package and timestamp distributables (nsis on win, tar on
    posix)
    """

    if os.name == 'nt':
        print PPF, 'Rebasing DLL / PYD files'
        # get list of pyd / dll files, add newline to each and every
        # filename
        so_files = ['%s\n' % (i,) for i in
                find_files(md_paths.pyi_dist_dir)]

        # open file in specfile_dir, write the whole list
        dll_list_fn = os.path.join(
                md_paths.specfile_dir, 'dll_list.txt')
        dll_list = file(dll_list_fn, 'w')
        dll_list.writelines(so_files)
        dll_list.close()

def windows_prereq_check():
    print PPF, 'WINDOWS prereq check'

    # if you give rebase any other command-line switches (even /?) it
    # exits with return code 99 and outputs its stuff to stderr
    # with -b it exits with return code 0 (expected) and uses stdout
    v = find_command_with_ver(
            'Microsoft Rebase (rebase.exe)', 'rebase -b 0x60000000',
            '^(REBASE):\s+Total.*$')

    return v


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
        return 1

    # dependency checking
    if os.name == 'nt':
        if not windows_prereq_check():
            print PPF, "ERR: Windows prerequisites do not check out."
            return 1


    md_paths = MDPaths(spec, pyi_script)

    #clean_pyinstaller(md_paths)
    #run_pyinstaller(md_paths)

    package_dist(md_paths)    



if __name__ == '__main__':
    main()

