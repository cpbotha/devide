# moduleKits __init__.py
# $Id$

"""Top-level __init__ of the module_kits.

@ivar module_kits_list: All moduleKits in this list will have their init()s
called with the moduleManager as parameter (after being imported).  Before
this happens though, members of this list that are also in the no-kits list
(defined by defaults.py or command-line) will be removed.

@ivar crucial_kits: Usually, when a kit raises an exception during its init()
call, this is ignored and DeVIDE starts up as usual.  However, if the module
is in the crucial_kit_list, DeVIDE will refuse to start up.
"""

module_kit_list = ['wxpython_kit', 'vtk_kit', 'vtktud_kit',
                   'itk_kit', 'matplotlib_kit']

crucial_kit_list = ['wxpython_kit', 'vtk_kit']

