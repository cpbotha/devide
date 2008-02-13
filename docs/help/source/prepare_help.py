# python rules.  severely.
# (c) 2007 cpbotha

import glob
import sys
import os
import shutil
import zipfile

def main():
    cwd = os.path.abspath(os.curdir)
    hhp_dir = os.path.join(cwd, 'devidehelp_tmphhp')

    os.chdir(hhp_dir)

    htb_list = glob.glob('*.html') +  \
        glob.glob('*.png') + \
        glob.glob('devide.hh?') + \
        ['CSHelp.txt']

    zf = zipfile.ZipFile('../../devide.htb', 'w', zipfile.ZIP_DEFLATED)
    for fn in htb_list:
        zf.write(fn)

    zf.close()

    # also copy the CHM file for the windows people.
    shutil.copy('devide.chm', '../../')


if __name__ == '__main__':
    main()

