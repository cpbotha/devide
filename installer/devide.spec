# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.


# RESTRUCTURE:
# * remove_binaries (startswith and contains)
# * remove_pure (startswith and contains)


# NB: stay away from any absolute path dependencies!!!

import os
import fnmatch
import re
import sys

def helper_remove_start(name, remove_names):
    """Helper function used to remove libraries from list.

    Returns true of name starts with anything from remove_names.
    """
    name = name.lower()    
    for r in remove_names:
        if name.startswith(r.lower()):
            return True

    return False

def helper_remove_finds(name, remove_finds):
    """Helper function that returns true if any item in remove_finds
    (list) can be string-found in name.  Everything is lowercased.
    """
    name = name.lower()
    for r in remove_finds:
        if name.find(r.lower()) >= 0:
            return True

    return False

def helper_remove_regexp(name, remove_regexps):
    """Helper function to remove things from list.

    Returns true if name matches any regexp in remove_regexps.
    """

    for r in remove_regexps:
        if re.match(r, name) is not None:
            return True

    return False

# argv[0] is the name of the Build.py script
INSTALLER_DIR = os.path.abspath(os.path.dirname(sys.argv[0]))
# argv[1] is the name of the spec file
# first we get the path of the spec file, then we have to go one up
specpath = os.path.abspath(os.path.dirname(sys.argv[1]))
APP_DIR = os.path.split(specpath)[0]

from distutils import sysconfig
MPL_DATA_DIR = os.path.join(sysconfig.get_python_lib(), 'matplotlib/mpl-data')

if sys.platform.startswith('win'):
    exeName = 'builddevide/devide.exe'

    extraLibs = []
    # we can keep msvcr71.dll and msvcp71.dll, in fact they should just
    # go in the installation directory with the other DLLs, see:
    # http://msdn.microsoft.com/library/default.asp?url=/library/en-us/
    # vclib/html/_crt_c_run.2d.time_libraries.asp
    remove_binaries = ['dciman32.dll', 'ddraw.dll', 'glu32.dll', 'msvcp60.dll',
                       'netapi32.dll', 'opengl32.dll', 'uxtheme.dll']
    
else:
    exeName = 'builddevide/devide'

    # under some linuxes, libpython is shared -- McMillan installer doesn't 
    # know about this...
    extraLibs = []

    # i'm hoping this isn't necessary anymore!
    if False: 
        vi = sys.version_info
        if (vi[0], vi[1]) == (2,4):
            # ubuntu hoary
            extraLibs = [('libpython2.4.so.1.0', '/usr/lib/libpython2.4.so.1.0', 'BINARY')]

        elif (vi[0], vi[1]) == (2,2) and \
                 os.path.exists('/usr/lib/libpython2.2.so.0.0'):
            # looks like debian woody
            extraLibs = [('libpython2.2.so.0.0', '/usr/lib/libpython2.2.so.0.0',
                          'BINARY')]

        # RHEL3 64 has a static python library.

    #####################################################################
    # on ubuntu 6.06, libdcmdata.so.1 and libofstd.so.1 could live in
    # /usr/lib, and are therefore thrown out by the McMillan Installer

    if os.path.exists('/usr/lib/libdcmdata.so.1') and \
       os.path.exists('/usr/lib/libofstd.so.1'):
        extraLibs.append(
            ('libdcmdata.so.1', '/usr/lib/libdcmdata.so.1', 'BINARY'))

        extraLibs.append(
            ('libofstd.so.1', '/usr/lib/libofstd.so.1','BINARY'))

    ######################################################################
    # to get this to work on Debian 3.1, we also need to ship libstdc++
    # and libXinerama
    # FIXME: figure some other way out to include the CORRECT libstdc++,
    # the previous hardcoding of this caused problems with the VL-e POC

    stdc = '/usr/lib/libstdc++.so.6'
    if os.path.exists(stdc):
	extraLibs.append((os.path.basename(stdc), stdc, 'BINARY'))

    xine = '/usr/lib/libXinerama.so.1'
    if os.path.exists(xine):
	extraLibs.append((os.path.basename(xine), xine, 'BINARY'))

    ######################################################################
    # ubuntu 7.10 has renumbered libtiff 3.7 (or .8) to 4.  other dists of
    # course don't have this, so we have to include it.
    libtiff = '/usr/lib/libtiff.so.4'
    if os.path.exists(libtiff):
        extraLibs.append(
                (os.path.basename(libtiff), libtiff, 'BINARY'))

    
    ######################################################################
    # also add some binary dependencies of numpy that are normally ignored
    # because they are in /lib and/or /usr/lib (see excludes in bindepend.py)
    from distutils import sysconfig
    npdir = os.path.join(sysconfig.get_python_lib(), 'numpy')
    ladir = os.path.join(npdir, 'linalg')
    lplpath = os.path.join(ladir, 'lapack_lite.so')
    # use mcmillan function to get LDD dependencies of lapack_lite.so
    import bindepend
    lpl_deps = bindepend.getImports(lplpath)
    for d in lpl_deps:
        if d.find('lapack') > 0 or d.find('blas') > 0 or \
           d.find('g2c') > 0 or d.find('atlas') > 0:
              extraLibs.append(
                 (os.path.basename(d), d, 'BINARY'))
                 
    # end numpy-dependent extraLibs section
    ##################################################################
                 
    # these libs will be removed from the package
    remove_binaries = ['libdl.so', 'libutil.so', 'libm.so', 'libc.so',
                       'libGLU.so', 'libGL.so', 'libGLcore.so', 
                       'libnvidia-tls.so',
                       'ld-linux-x86-64.so.2', 'libgcc_s.so',
                       'libtermcap',
                       'libXft.so', 'libXrandr.so', 'libXrender.so',
                       'libpthread.so', 'libreadline.so',
                       'libICE.so',
                       'libSM.so', 'libX11.so',
                       'libXext.so', 'libXi.so', 
                       'libXt.so',
                       'libpango', 'libfontconfig', 'libfreetype',
                       'libatk', 'libgtk', 'libgdk',
                       'libglib', 'libgmodule', 'libgobject', 'libgthread',
                       'qt', '_tkinter']

    # make sure remove_binaries is lowercase
    remove_binaries = [i.lower() for i in remove_binaries]

# global removes: we want to include this file so that the user can edit it
#remove_binaries += ['defaults.py']

# we have to remove these nasty built-in dependencies EARLY in the game
dd = config['EXE_dependencies']
newdd = [i for i in dd
         if not helper_remove_start(i[0].lower(), remove_binaries)]
config['EXE_dependencies'] = newdd


print "[*] APP_DIR == %s" % (APP_DIR)
print "[*] exeName == %s" % (exeName)
mainScript = os.path.join(APP_DIR, 'devide.py')
print "[*] mainScript == %s" % (mainScript)

# generate available kit list #########################################
# simple form of the checking done by the module_kits package itself

sys.path.insert(0, APP_DIR)

import module_kits

#######################################################################

# segments
segTree = Tree(os.path.join(APP_DIR, 'segments'), 'segments', ['.svn'])
# snippets
snipTree = Tree(os.path.join(APP_DIR, 'snippets'), 'snippets', ['.svn']) 
# arb data
dataTree = Tree(os.path.join(APP_DIR, 'data'), 'data', ['.svn'])
# documents and help, exclude help source
docsTree = Tree(os.path.join(APP_DIR, 'docs'), 'docs', ['.svn', 'source'])

# all modules
modules_tree = Tree(os.path.join(APP_DIR, 'modules'), 'modules',
                    ['.svn', '*~'])

# all module_kits
module_kits_tree = Tree(os.path.join(APP_DIR, 'module_kits'), 'module_kits',
                    ['.svn', '*~'])

print "===== APP_DIR: ", APP_DIR

# VTKPIPELINE ICONS

# unfortunately, due to the vtkPipeline design, these want to live one
# down from the main dir
vpli_dir = os.path.join(APP_DIR, 'external/vtkPipeline/Icons')
vpli = [(os.path.join('Icons', i),
         os.path.join(vpli_dir, i), 'DATA')
        for i in os.listdir(vpli_dir) if fnmatch.fnmatch(i, '*.xpm')]

# MATPLOTLIB data dir
mpl_data_dir = Tree(MPL_DATA_DIR, 'matplotlibdata')

if False:
    from distutils import sysconfig
    numpy_tree = Tree(
        os.path.join(sysconfig.get_python_lib(),'numpy'),
        prefix=os.path.join('module_kits','numpy_kit','numpy'), 
        excludes=['*.pyc', '*.pyo', 'doc', 'docs'])

testing_tree = Tree(os.path.join(APP_DIR, 'testing'), 'testing',
                    ['.svn', '*~', '*.pyc'])

# and some miscellaneous files
misc_tree = [('devide.cfg', '%s/devide.cfg' % (APP_DIR,), 'DATA')]

##########################################################################

SUPPORT_DIR = os.path.join(INSTALLER_DIR, 'support')

a = Analysis([os.path.join(SUPPORT_DIR, '_mountzlib.py'),
              os.path.join(SUPPORT_DIR, 'useUnicode.py'),
              mainScript],
             pathex=[],
             hookspath=[os.path.join(APP_DIR, 'installer', 'hooks')])

######################################################################
# sanitise a.pure
remove_pure_finds = []
# we remove all module and module_kits based things, because they're
# taken care of by hooks/hook-moduleManager.py
# we also remove itk (it seems to be slipping in in spite of the fact
# that I'm explicitly excluding it from module_kits)
remove_pure_starts = ['modules.', 'module_kits', 'testing', 'itk']

for i in range(len(a.pure)-1, -1, -1):
    if helper_remove_finds(a.pure[i][1], remove_pure_finds) or \
       helper_remove_start(a.pure[i][0], remove_pure_starts):
        del a.pure[i]
        
######################################################################
# sanitise a.binaries

remove_binary_finds = []

for i in range(len(a.binaries)-1, -1, -1):
    if helper_remove_finds(a.binaries[i][1], remove_binaries) or \
       helper_remove_start(a.binaries[i][0], remove_binary_finds):
        del a.binaries[i]

######################################################################

# create the compressed archive with all the other pyc files
# will be integrated with EXE archive
pyz = PYZ(a.pure)

# in Installer 6a2, the -f option is breaking things (the support directory
# is deleted after the first invocation!)
#options = [('f','','OPTION')] # LD_LIBRARY_PATH is correctly set on Linux
#options = [('v', '', 'OPTION')]     # Python is ran with -v
options = []

# because we've already modified the config, we won't be pulling in
# hardcoded dependencies that we don't want.
exe = EXE(pyz,
          a.scripts + options,
          exclude_binaries=1,
          name=exeName,
          icon=os.path.join(APP_DIR, 'resources/graphics/devidelogo64x64.ico'),
          debug=0,
          strip=0,
          console=True)


all_binaries = a.binaries + modules_tree + module_kits_tree + vpli + \
    mpl_data_dir + \
    extraLibs + segTree + snipTree + dataTree + docsTree + misc_tree + \
    testing_tree

coll = COLLECT(exe,
               all_binaries,
               strip=0,
               name='distdevide')

# wrapitk_tree is packaged completely separately

