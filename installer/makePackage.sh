#!/bin/bash
# $Id: makePackage.sh,v 1.2 2003/04/28 20:55:22 cpbotha Exp $

# go to the directory that contains makePackage.sh (i.e. dscas3/installer)
cd `dirname $0`

# nuke all .pyc files (to be sure)
find ../ -name "*.pyc" -exec rm {} \;

# remove build directories so that we are assured of a clean start
rm -rf distdscas3
rm -rf builddscas3

# run the McMillan Installer
if [ `uname` == Linux ]; then

INSTALLER='python /home/cpbotha/build/Installer/Build.py'
$INSTALLER dscas3.spec
# strip all the libraries
strip distdscas3/*.so
# make a tarball
mv distdscas3 dscas3
tar czvf "dscas3-`date +%Y%m%d`.tar.gz" dscas3
mv dscas3 distdscas3

else

INSTALLER='python c:/build/Installer/Build.py'
$INSTALLER dscas3.spec
# make an archive
mv distdscas3 dscas3
zip -rp "dscas3-win32-`date +%Y%m%d`.zip" dscas3
mv dscas3 distdscas3

fi
