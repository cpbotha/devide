# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.


# Run python on this file to allow PyChecker to check devide

#__pychecker__ = '--config pycheckrc'

print "doPyChecker.py starting (output redirected to doPyChecker.out)..."

import sys
sof = open('doPyChecker.out', 'w')
stdout = sys.stdout
sys.stdout = sof

import pychecker.checker
import devide

from modules import module_list
for d3mName in module_list:
    print d3mName
    exec('import modules.%s' % (d3mName,))

sys.stdout = stdout
sof.close()

print "doPyChecker.py DONE."
