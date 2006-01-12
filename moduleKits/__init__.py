# moduleKits __init__.py
# $Id: __init__.py,v 1.7 2006/01/12 13:19:21 cpbotha Exp $

"""Top-level __init__ of the module_kits.

@ivar module_kits_list:
@ivar crucial_kits: 
"""

# all moduleKits in this list will have their init()s called with the
# moduleManager as parameter (after being imported)
# before this happens though, members of this list that are also in the
# no-kits list (defined by defaults.py or command-line) will be removed
moduleKitList = ['vtkKit', 'itkKit']


crucialKits = ['vtkKit']

