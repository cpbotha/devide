import os
import fnmatch
import sys

if sys.platform.startswith('win'):
    INSTALLER_DIR = 'c:\\build\\Installer'
    D3_DIR = 'c:\\work\\code\\dscas3'
    exeName = 'builddscas3/dscas3.exe'    
else:
    INSTALLER_DIR = '/home/cpbotha/build/Installer'
    D3_DIR = '/home/cpbotha/work/code/dscas3'
    exeName = 'builddscas3/dscas3'

print "[*] D3_DIR == %s" % (D3_DIR)
print "[*] exeName == %s" % (exeName)
mainScript = os.path.join(D3_DIR, 'dscas3.py')
print "[*] mainScript == %s" % (mainScript)

# USER MODULES

umod_dir = os.path.join(D3_DIR, 'userModules')
umods = [(os.path.join('userModules', i), os.path.join(umod_dir, i), 'DATA')
         for i in os.listdir(umod_dir) if fnmatch.fnmatch(i, '*.py')]

# VTKPIPELINE ICONS

# unfortunately, due to the vtkPipeline design, these want to live one
# down from the main dir
vpli_dir = os.path.join(D3_DIR, 'external/vtkPipeline/Icons')
vpli = [(os.path.join('Icons', i),
         os.path.join(vpli_dir, i), 'DATA')
        for i in os.listdir(vpli_dir) if fnmatch.fnmatch(i, '*.xpm')]

if sys.platform.startswith('win'):
    extraLibs = []
    removeLibs = []
else:
    # under linux, libpython is shared -- McMillan installer doesn't know
    # about this...
    # also copy the hdf libs
    extraLibs = [('libpython2.2.so.0.0', '/usr/lib/libpython2.2.so.0.0',
                  'BINARY'),
                 ('libmfhdf.so.4', '/usr/lib/libmfhdf.so.4','BINARY'),
                 ('libdf.so.4', '/usr/lib/libdf.so.4','BINARY')]
    
    # these libs will be removed from the package
    removeLibs = [('libGLU.so.1', '', ''), ('libICE.so.6','',''),
                  ('libSM.so.6', '', ''), ('libX11.so.6', '', ''), 
                  ('libXext.so.6', '', ''), ('libXi.so.6', '', ''), 
                  ('libXt.so.6', '', '')]

##########################################################################

SUPPORT_DIR = os.path.join(INSTALLER_DIR, 'support')
a = Analysis([os.path.join(SUPPORT_DIR, '_mountzlib.py'),
              os.path.join(SUPPORT_DIR, 'useUnicode.py'),
              mainScript],
             pathex=[],
             hookspath=[os.path.join(D3_DIR, 'installer\\hooks\\')])

pyz = PYZ(a.pure)


    
exe = EXE(pyz,
          a.scripts, #+ [('v', '', 'OPTION')],
          exclude_binaries=1,
          name=exeName,
          debug=0,
          strip=0,
          console=1 )

coll = COLLECT( exe,
               a.binaries + umods + vpli,
               strip=0,
               name='distdscas3')
