#FIXME FIXME FIXME:
#* think up solution for dicom.dic problem.

D3_DIR = '/home/cpbotha/work/code/dscas3'

import os
import fnmatch

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

# under linux, libpython is shared -- McMillan installer doesn't know
# about this...
# also copy the hdf libs
extraLibs = [('libpython2.2.so.0.0', '/usr/lib/libpython2.2.so.0.0','BINARY'),
    ('libmfhdf.so.4', '/usr/lib/libmfhdf.so.4','BINARY'),
    ('libdf.so.4', '/usr/lib/libdf.so.4','BINARY')]
    
# these libs will be removed from the package
removeLibs = [('libGLU.so.1', '', ''), ('libICE.so.6','',''),
              ('libSM.so.6', '', ''), ('libX11.so.6', '', ''), 
              ('libXext.so.6', '', ''), ('libXi.so.6', '', ''), 
              ('libXt.so.6', '', '')]

##########################################################################

a = Analysis(['/home/cpbotha/build/Installer/support/_mountzlib.py',
    	      '/home/cpbotha/build/Installer/support/useUnicode.py',
              '/home/cpbotha/work/code/dscas3/dscas3.py'],
             pathex=[],
             hookspath=['/home/cpbotha/work/code/dscas3/installer/hooks'])

pyz = PYZ(a.pure)

exe = EXE(pyz,
          a.scripts, #+ [('v', '', 'OPTION')], # for debugging of lib loading
          exclude_binaries=1,
          name='builddscas3/dscas3',
          debug=0, # switch on for more debugging info
          console=1)

coll = COLLECT(exe,
               a.binaries - removeLibs + umods + vpli + extraLibs,
               name='distdscas3')
