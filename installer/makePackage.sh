#!/bin/bash
# $Id: makePackage.sh,v 1.1 2003/03/13 11:06:19 cpbotha Exp $

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

INSTALLER='python somethingElse';

fi
