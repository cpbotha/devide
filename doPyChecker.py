# doPyChecker.py copyright (c) 2003 by Charl P. Botha cpbotha@ieee.org
# $Id: doPyChecker.py,v 1.1 2003/08/27 12:17:59 cpbotha Exp $
# Run python on this file to allow PyChecker to check dscas3

#__pychecker__ = '--config pycheckrc'

import pychecker.checker
import dscas3

from modules import module_list
for d3mName in module_list:
    print d3mName
    exec('import modules.%s' % (d3mName,))
