D3_DIR = '/home/cpbotha/work/code/dscas3'

import os
import fnmatch

# MAIN APPLICATIONS XRCS 

# let's build up list of xml resources
# even better, let's just make the list of installer TOC tuples, each
# consisting of (NAME, PATH, TYPECODE)
mx_dir = os.path.join(D3_DIR, 'resources/xml')
# note that the first element of the tuple is the name RELATIVE to the
# execution "top-level"
main_xrcs = [(os.path.join('resources/xml', i), os.path.join(mx_dir, i),'DATA')
             for i in os.listdir(mx_dir) if fnmatch.fnmatch(i, '*xrc')]

# USER MODULES

umod_dir = os.path.join(D3_DIR, 'user_modules')
umods = [(os.path.join('user_modules', i), os.path.join(umod_dir, i), 'DATA')
         for i in os.listdir(umod_dir) if fnmatch.fnmatch(i, '*.py')]

# INTERNAL MODULE XRCS

modx_dir = os.path.join(D3_DIR, 'modules/resources/xml')
mod_xrcs = [(os.path.join('modules/resources/xml', i),
             os.path.join(modx_dir, i), 'DATA')
            for i in os.listdir(modx_dir) if fnmatch.fnmatch(i, '*.xrc')]


# VTKPIPELINE ICONS

# unfortunately, due to the vtkPipeline design, these want to live one
# down from the main dir
vpli_dir = os.path.join(D3_DIR, 'external/vtkPipeline/Icons')
vpli = [(os.path.join('Icons', i),
         os.path.join(vpli_dir, i), 'DATA')
        for i in os.listdir(vpli_dir) if fnmatch.fnmatch(i, '*.xpm')]


##########################################################################

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
               a.binaries + main_xrcs + mod_xrcs + umods + vpli,
               name='distdscas3')
