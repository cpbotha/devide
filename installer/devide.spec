import os
import fnmatch
import sys

def remove(name, removeNames):
    """Helper function used to remove libraries from list.
    """
    
    for r in removeNames:
        if name.startswith(r):
            return True

    return False


if sys.platform.startswith('win'):
    INSTALLER_DIR = 'c:\\build\\Installer'
    APP_DIR = 'c:\\work\\code\\devide'
    exeName = 'builddevide/devide.exe'

    extraLibs = []
    # we can keep msvcr71.dll and msvcp71.dll, in fact they should just
    # go in the installation directory with the other DLLs, see:
    # http://msdn.microsoft.com/library/default.asp?url=/library/en-us/
    # vclib/html/_crt_c_run.2d.time_libraries.asp
    removeNames = ['dciman32.dll', 'ddraw.dll', 'glu32.dll', 'msvcp60.dll',
                   'netapi32.dll', 'opengl32.dll']
    
else:
    INSTALLER_DIR = '/home/cpbotha/build/Installer'
    APP_DIR = '/home/cpbotha/work/code/devide'
    exeName = 'builddevide/devide'

    # under some linuxes, libpython is shared -- McMillan installer doesn't 
    # know about this...
    extraLibs = []
    
    vi = sys.version_info
    if (vi[0], vi[1]) == (2,4):
        # ubuntu hoary
        extraLibs = [('libpython2.4.so', '/usr/lib/libpython2.4.so', 'BINARY')]

    elif (vi[0], vi[1]) == (2,2) and \
             os.path.exists('/usr/lib/libpython2.2.so.0.0'):
        # looks like debian woody
        extraLibs = [('libpython2.2.so.0.0', '/usr/lib/libpython2.2.so.0.0',
                      'BINARY')]

    # RHEL3 64 has a static python library.
    
    # these libs will be removed from the package
    removeNames = ['libdl.so', 'libutil.so', 'libm.so', 'libc.so',
                   'libGLU.so', 'libGL.so', 'libGLcore.so', 
                   'libnvidia-tls.so',
                   'ld-linux-x86-64.so.2', 'libgcc_s.so',
                   'libstdc++.so', 'libtermcap',
                   'libXft.so', 'libXrandr.so', 'libXrender.so',
                   'libpthread.so', 'libreadline.so',
                   'libICE.so',
                   'libSM.so', 'libX11.so',
                   'libXext.so', 'libXi.so', 
                   'libXt.so',
                   'libpango', 'libfontconfig', 'libfreetype',
                   'libatk', 'libgtk', 'libgdk',
                   'libglib', 'libgmodule', 'libgobject', 'libgthread',
                   'libjpeg', 'libpng', 'libtiff', 'libz.so', 'libexpat']

    # make sure removeNames is lowercase
    removeNames = [i.lower() for i in removeNames]    


# we have to remove these nasty built-in dependencies EARLY in the game
dd = config['EXE_dependencies']

    
newdd = [i for i in dd if not remove(i[0].lower(), removeNames)]
config['EXE_dependencies'] = newdd


print "[*] APP_DIR == %s" % (APP_DIR)
print "[*] exeName == %s" % (exeName)
mainScript = os.path.join(APP_DIR, 'devide.py')
print "[*] mainScript == %s" % (mainScript)

# segments
segTree = Tree(os.path.join(APP_DIR, 'segments'), 'segments', ['CVS'])
# snippets
snipTree = Tree(os.path.join(APP_DIR, 'snippets'), 'snippets', ['CVS']) 
# arb data
dataTree = Tree(os.path.join(APP_DIR, 'data'), 'data', ['CVS'])
# documents and help, exclude help source
docsTree = Tree(os.path.join(APP_DIR, 'docs'), 'docs', ['CVS', 'source'])

# USER MODULES
userModulesTree = Tree(os.path.join(APP_DIR, 'userModules'), 'userModules',
                       ['CVS', '*~'])

# the extra modulePacks
modulePacksTree = Tree(os.path.join(APP_DIR, 'modulePacks'), 'modulePacks',
                       ['CVS', '*~'])

# VTKPIPELINE ICONS

# unfortunately, due to the vtkPipeline design, these want to live one
# down from the main dir
vpli_dir = os.path.join(APP_DIR, 'external/vtkPipeline/Icons')
vpli = [(os.path.join('Icons', i),
         os.path.join(vpli_dir, i), 'DATA')
        for i in os.listdir(vpli_dir) if fnmatch.fnmatch(i, '*.xpm')]

##########################################################################

SUPPORT_DIR = os.path.join(INSTALLER_DIR, 'support')
a = Analysis([os.path.join(SUPPORT_DIR, '_mountzlib.py'),
              os.path.join(SUPPORT_DIR, 'useUnicode.py'),
              mainScript],
             pathex=[],
             hookspath=[os.path.join(APP_DIR, 'installer/hooks/')])

pyz = PYZ(a.pure)

# in Installer 6a2, the -f option is breaking things (the support directory
# is deleted after the first invocation!)
#options = [('f','','OPTION')] # LD_LIBRARY_PATH is correctly set on Linux
#options += [('v', '', 'OPTION')]     # Python is ran with -v

# because we've already modified the config, we won't be pulling in
# hardcoded dependencies that we don't want.
exe = EXE(pyz,
          a.scripts, #+ options,
          exclude_binaries=1,
          name=exeName,
          icon=os.path.join(APP_DIR, 'resources/graphics/devidelogo64x64.ico'),
          debug=0,
          strip=0,
          console=1 )

# we do it this way so that removeLibs doesn't have to be case-sensitive
# first add together everything that we want to ship
allBinaries = a.binaries + userModulesTree + modulePacksTree + vpli + \
              extraLibs + segTree + snipTree + dataTree + docsTree


# make new list of 3-element tuples of shipable things
binaries = [i for i in allBinaries if not remove(i[0].lower(), removeNames)]

coll = COLLECT(exe,
               binaries,
               strip=0,
               name='distdevide')


