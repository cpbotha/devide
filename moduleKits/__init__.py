# moduleKits __init__.py
# $Id: __init__.py,v 1.3 2005/11/15 09:03:29 cpbotha Exp $
# modify this file when you add a new moduleKit: add the kitname to the list
# of import and to the moduleKitList variable.

import vtkKit
import itkKit

# all moduleKits in this list will have their init()s called with the
# moduleManager as parameter.
moduleKitList = ['vtkKit', 'itkKit']

