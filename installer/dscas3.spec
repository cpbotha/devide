D3_DIR = '/home/cpbotha/work/code/dscas3'

import os
import fnmatch

# USER MODULES

umod_dir = os.path.join(D3_DIR, 'user_modules')
umods = [(os.path.join('user_modules', i), os.path.join(umod_dir, i), 'DATA')
         for i in os.listdir(umod_dir) if fnmatch.fnmatch(i, '*.py')]

# VTKPIPELINE ICONS

# unfortunately, due to the vtkPipeline design, these want to live one
# down from the main dir
vpli_dir = os.path.join(D3_DIR, 'external/vtkPipeline/Icons')
vpli = [(os.path.join('Icons', i),
         os.path.join(vpli_dir, i), 'DATA')
        for i in os.listdir(vpli_dir) if fnmatch.fnmatch(i, '*.xpm')]


##########################################################################

a = Analysis(['/home/cpbotha/build/Installer/support/_mountzlib.py',
    	      '/home/cpbotha/build/Installer/support/useUnicode.py',
              '/home/cpbotha/work/code/dscas3/dscas3.py'],
             pathex=['/home/cpbotha/work/code/dscas3/modules'],
             hookspath=['/home/cpbotha/work/code/dscas3/installer/hooks'])

pyz = PYZ(a.pure)

exe = EXE(pyz,
          a.scripts, #+ [('v', '', 'OPTION')], # for debugging of lib loading
          exclude_binaries=1,
          name='builddscas3/dscas3',
          debug=0, # switch on for more debugging info
          console=1)

coll = COLLECT(exe,
               a.binaries + umods + vpli,
               name='distdscas3')
