# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

import getopt
import os
import re
import shutil
import sys

###################################################################
# the following programmes should either be on your path, or you
# should specify the full paths here.
# Microsoft utility to rebase files.
REBASE = "rebase"

# end of programmes ###############################################

PPF = "[*** DeVIDE make_dist ***]"
S_PPF = "%s =====>>>" % (PPF,) # used for stage headers

S_CLEAN_PYI = 'clean_pyi'
S_RUN_PYI = 'run_pyi'
S_WRAPITK_TREE = 'wrapitk_tree'
S_REBASE_DLLS = 'rebase_dlls'
S_PACKAGE_DIST = 'package_dist'
DEFAULT_STAGES = '%s, %s, %s, %s, %s' % \
        (S_CLEAN_PYI, S_RUN_PYI, S_WRAPITK_TREE, 
                S_REBASE_DLLS, S_PACKAGE_DIST)





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
is the directory containing the devide source that you are using to
build the distributables.

Other switches:
--stages : by default all stages are run.  With this parameter, a
           subset of the stages can be specified.  The full list is: 
           %s
""" % (DEFAULT_STAGES,)

    print message

def clean_pyinstaller(md_paths):
    """Clean out pyinstaller dist and build directories so that it has
    to do everything from scratch.  We usually do this before building
    full release versions.
    """

    print S_PPF, "clean_pyinstaller"
    
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

    print S_PPF, "run_pyinstaller"

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

    print S_PPF, "package_dist"

def rebase_dlls(md_paths):
    """Rebase all DLLs in the distdevide tree on Windows.
    """

    if os.name == 'nt':
        print S_PPF, "rebase_dlls"
        # get list of pyd / dll files, add newline to each and every
        # filename
        so_files = ['%s\n' % (i,) for i in
                find_files(md_paths.pyi_dist_dir)]

        print "Found %d DLL PYD files..." % (len(so_files),)

        # open file in specfile_dir, write the whole list
        dll_list_fn = os.path.join(
                md_paths.specfile_dir, 'dll_list.txt')
        dll_list = file(dll_list_fn, 'w')
        dll_list.writelines(so_files)
        dll_list.close()

        # now run rebase on the list
        os.chdir(md_paths.specfile_dir)
        ret = os.system(
                '%s -b 0x60000000 -e 0x1000000 @dll_list.txt -v' %
                (REBASE,))

        # rebase returns 99 after rebasing, no idea why.
        if ret != 99:
            raise RuntimeError('Could not rebase DLLs.')

def wrapitk_tree(md_paths):
    print S_PPF, "wrapitk_tree"

    py_file = os.path.join(md_paths.specfile_dir, 'wrapitk_tree.py')
    cmd = "%s %s %s" % (sys.executable, py_file, md_paths.pyi_dist_dir) 
    ret = os.system(cmd)

    if ret != 0:
        raise RuntimeError(
        'Error creating self-contained WrapITK tree.')


def windows_prereq_check():
    print PPF, 'WINDOWS prereq check'

    # if you give rebase any other command-line switches (even /?) it
    # exits with return code 99 and outputs its stuff to stderr
    # with -b it exits with return code 0 (expected) and uses stdout
    v = find_command_with_ver(
            'Microsoft Rebase (rebase.exe)', 
            '%s -b 0x60000000' % (REBASE,),
            '^(REBASE):\s+Total.*$')

    return v


def main():
    try:
        optlist, args = getopt.getopt(
                sys.argv[1:], 'hs:i:',
                ['help', 'spec=','pyinstaller-script=','stages='])

    except getopt.GetoptError,e:
        usage
        return

    spec = None
    pyi_script = None
    stages = DEFAULT_STAGES
    

    for o, a in optlist:
        if o in ('-h', '--help'):
            usage()
            return

        elif o in ('-s', '--spec'):
            spec = a

        elif o in ('-i', '--pyinstaller-script'):
            pyi_script = a

        elif o in ('--stages'):
            stages = a
            

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

    stages = [i.strip() for i in stages.split(',')]

    if S_CLEAN_PYI in stages:
        clean_pyinstaller(md_paths)
    if S_RUN_PYI in stages:
        run_pyinstaller(md_paths)
    if S_WRAPITK_TREE in stages:
        wrapitk_tree(md_paths)
    if S_REBASE_DLLS in stages:
        rebase_dlls(md_paths)
    if S_PACKAGE_DIST in stages:
        package_dist(md_paths)    



if __name__ == '__main__':
    main()

