# moduleKits __init__.py
# $Id: __init__.py,v 1.2 2005/11/13 16:55:02 cpbotha Exp $
# modify this file when you add a new moduleKit: add the kitname to the list
# of import and to the moduleKitList variable.

import vtkKit

# all moduleKits in this list will have their init()s called with the
# moduleManager as parameter.
moduleKitList = ['vtkKit']

