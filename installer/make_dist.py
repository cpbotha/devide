# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

import getopt
import os
import sys

def usage():
    message = """
make_dist.py - build DeVIDE distributables.

Invoke as follows:
python make_dist.py -s specfile -i installer_script
where specfile is the pyinstaller spec file and installer_script
refers to the full path of the pyinstaller Build.py 

The specfile should be in the directory devide/installer, where devide
contains the devide source that you are using to build the
distributables.
"""

def main():
    try:
        optlist, args = getopt.getopt(
                sys.argv[1:], 'hs:i:',
                ['help', 'spec=','pyinstaller-script='])

    except getopt.GetoptError,e:
        usage
        return

    spec = None
    pyi_script = None

    for o, a in optlist:
        if o in ('-h', '--help'):
            usage()
            return

        elif o in ('-s', '--spec'):
            spec = a

        elif o in ('-i', '--pyinstaller-script'):
            pyi_script = a

    if spec is None or pyi_script is None:
        # we need BOTH the specfile and pyinstaller script
        usage()
        return





if __name__ == '__main__':
    main()

