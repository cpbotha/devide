# doPyChecker.py copyright (c) 2003 by Charl P. Botha cpbotha@ieee.org
# $Id: doPyChecker.py,v 1.2 2003/08/27 12:34:36 cpbotha Exp $
# Run python on this file to allow PyChecker to check dscas3

#__pychecker__ = '--config pycheckrc'

print "doPyChecker.py starting (output redirected to doPyChecker.out)..."

import sys
sof = open('doPyChecker.out', 'w')
stdout = sys.stdout
sys.stdout = sof

import pychecker.checker
import dscas3

from modules import module_list
for d3mName in module_list:
    print d3mName
    exec('import modules.%s' % (d3mName,))

sys.stdout = stdout
sof.close()

print "doPyChecker.py DONE."
