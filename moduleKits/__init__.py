# moduleKits __init__.py
# $Id: __init__.py,v 1.6 2005/11/20 21:54:17 cpbotha Exp $
# modify this file when you add a new moduleKit: add the kitname to the list
# of import and to the moduleKitList variable.

# all moduleKits in this list will have their init()s called with the
# moduleManager as parameter (after being imported)
# before this happens though, members of this list that are also in the
# no-kits list (defined by defaults.py or command-line) will be removed
moduleKitList = ['vtkKit', 'itkKit']
