D3_DIR = '/home/cpbotha/work/code/dscas3'

import os
import fnmatch

# let's build up list of xml resources
# even better, let's just make the list of installer TOC tuples, each
# consisting of (NAME, PATH, TYPECODE)
mx_dir = os.path.join(D3_DIR, 'resources/xml')
# note that the first element of the tuple is the name RELATIVE to the
# executing "top-level"
main_xrcs = [(os.path.join('resources/xml', i), os.path.join(mx_dir, i),'DATA')
             for i in os.listdir(mx_dir) if fnmatch.fnmatch(i, '*xrc')]

umod_dir = os.path.join(D3_DIR, 'user_modules')
umods = [(os.path.join('user_modules', i), os.path.join(umod_dir, i), 'DATA')
         for i in os.listdir(umod_dir) if fnmatch.fnmatch(i, '*.py')]

modx_dir = os.path.join(D3_DIR, 'modules/resources/xml')
mod_xrcs = [(os.path.join('modules/resources/xml', i),
             os.path.join(modx_dir, i), 'DATA')
            for i in os.listdir(modx_dir) if fnmatch.fnmatch(i, '*.xrc')]


misc = [('user_modules/__init__.py',
         os.path.join(D3_DIR, 'user_modules/__init__.py'), 'DATA')]


a = Analysis(['/home/cpbotha/build/Installer/support/useUnicode.py',
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
               a.binaries + main_xrcs + mod_xrcs + umods + misc,
               name='distdscas3')
