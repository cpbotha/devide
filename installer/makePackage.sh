#!/bin/bash
# $Id: makePackage.sh,v 1.8 2004/04/15 12:51:00 cpbotha Exp $

# go to the directory that contains makePackage.sh (i.e. devide/installer)
cd `dirname $0`

# nuke all .pyc files (to be sure)
find ../ -name "*.pyc" -exec rm {} \;
# nuke all backup files
find ../ -name "*~" -exec rm {} \;
find ../ -name "#*#" -exec rm {} \;

# remove build directories so that we are assured of a clean start
rm -rf distdevide
rm -rf builddevide

# run the McMillan Installer
if [ `uname` == Linux ]; then

INSTALLER='python /home/cpbotha/build/Installer/Build.py'
$INSTALLER devide.spec
# strip all the libraries
strip distdevide/*.so
# remove rpath information (else the installation doesn't work everywhere)
chrpath --delete distdevide/*.so
# make a tarball
mv distdevide devide
rm -f devide.tar.gz
tar czvf "devide.tar.gz" devide
mv devide distdevide

else

INSTALLER='python c:/build/Installer/Build.py'
$INSTALLER devide.spec
# optionally make an archive
# mv distdevide devide
# zip -rp "devide-win32-`date +%Y%m%d`.zip" devide
# mv devide distdevide

fi
