# moduleKits __init__.py
# $Id$

"""Top-level __init__ of the module_kits.

@ivar module_kits_list: All moduleKits in this list will have their init()s
called with the moduleManager as parameter (after being imported).  Before
this happens though, members of this list that are also in the no-kits list
(defined by defaults.py or command-line) will be removed.  The kits will be
imported in the order that they are specified.  Make sure that kits dependent
on other kits occur after those kits in the list, the dependency checker is
that simple.  After all kit loading is complete, the module_kit_list will
contain the names of the kits that were successfully loaded.

@ivar crucial_kits: Usually, when a kit raises an exception during its init()
call, this is ignored and DeVIDE starts up as usual.  However, if the module
is in the crucial_kit_list, DeVIDE will refuse to start up.
"""

module_kit_list = ['wx_kit', 'vtk_kit', 'vtktud_kit',
                   'itk_kit', 'itktud_kit',
                   'numpy_kit', 'matplotlib_kit', 'stats_kit']

dependencies_dict = {'vtktud_kit' : ['vtk_kit'],
                     'matplotlib_kit' : ['numpy_kit'],
                     'itktud_kit' : ['itk_kit']}

crucial_kit_list = ['wx_kit', 'vtk_kit']

