import os
import fnmatch
import sys

if sys.platform.startswith('win'):
    INSTALLER_DIR = 'c:\\build\\Installer'
    D3_DIR = 'c:\\work\\code\\devide'
    exeName = 'builddevide/devide.exe'    
else:
    INSTALLER_DIR = '/home/cpbotha/build/Installer'
    D3_DIR = '/home/cpbotha/work/code/devide'
    exeName = 'builddevide/devide'

print "[*] D3_DIR == %s" % (D3_DIR)
print "[*] exeName == %s" % (exeName)
mainScript = os.path.join(D3_DIR, 'devide.py')
print "[*] mainScript == %s" % (mainScript)

# segments
segTree = Tree(os.path.join(D3_DIR, 'segments'), 'segments', ['CVS'])
# arb data
dataTree = Tree(os.path.join(D3_DIR, 'data'), 'data', ['CVS'])
# documents and help, exclude help source
docsTree = Tree(os.path.join(D3_DIR, 'docs'), 'docs', ['CVS', 'source'])

# USER MODULES
userModulesTree = Tree(os.path.join(D3_DIR, 'userModules'), 'userModules',
                       ['CVS', '*~'])

# the extra modulePacks
modulePacksTree = Tree(os.path.join(D3_DIR, 'modulePacks'), 'modulePacks',
                       ['CVS', '*~'])

# VTKPIPELINE ICONS

# unfortunately, due to the vtkPipeline design, these want to live one
# down from the main dir
vpli_dir = os.path.join(D3_DIR, 'external/vtkPipeline/Icons')
vpli = [(os.path.join('Icons', i),
         os.path.join(vpli_dir, i), 'DATA')
        for i in os.listdir(vpli_dir) if fnmatch.fnmatch(i, '*.xpm')]

if sys.platform.startswith('win'):
    extraLibs = []
    # we can keep msvcr71.dll and msvcp71.dll, in fact they should just
    # go in the installation directory with the other DLLs, see:
    # http://msdn.microsoft.com/library/default.asp?url=/library/en-us/
    # vclib/html/_crt_c_run.2d.time_libraries.asp
    removeNames = ['dciman32.dll', 'ddraw.dll', 'glu32.dll', 'msvcp60.dll',
                   'netapi32.dll', 'opengl32.dll']
else:
    # under linux, libpython is shared -- McMillan installer doesn't know
    # about this...
    extraLibs = [('libpython2.2.so.0.0', '/usr/lib/libpython2.2.so.0.0',
                  'BINARY')]
    
    # these libs will be removed from the package
    removeNames = ['libGLU.so.1', 'libICE.so.6',
                   'libSM.so.6', 'libX11.so.6',
                   'libXext.so.6', 'libXi.so.6', 
                   'libXt.so.6']

##########################################################################

SUPPORT_DIR = os.path.join(INSTALLER_DIR, 'support')
a = Analysis([os.path.join(SUPPORT_DIR, '_mountzlib.py'),
              os.path.join(SUPPORT_DIR, 'useUnicode.py'),
              mainScript],
             pathex=[],
             hookspath=[os.path.join(D3_DIR, 'installer/hooks/')])

pyz = PYZ(a.pure)


    
exe = EXE(pyz,
          a.scripts, #+ [('v', '', 'OPTION')], # Python is ran with -v
          exclude_binaries=1,
          name=exeName,
          icon=os.path.join(D3_DIR, 'resources/graphics/devidelogo64x64.ico'),
          debug=0,
          strip=0,
          console=1 )

# we do it this way so that removeLibs doesn't have to be case-sensitive
# first add together everything that we want to ship
allBinaries = a.binaries + userModulesTree + modulePacksTree + vpli + \
              extraLibs + segTree + dataTree + docsTree

# make sure removeNames is lowercase
removeNames = [i.lower() for i in removeNames]
# make new list of 3-element tuples of shipable things
binaries = [i for i in allBinaries if i[0].lower() not in removeNames]

coll = COLLECT(exe,
               binaries,
               strip=0,
               name='distdevide')

