#!/bin/bash
# $Id: makePackage.sh,v 1.10 2004/05/23 21:49:41 cpbotha Exp $

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
find distdevide/ -name *.so | xargs strip
# remove rpath information (else the installation doesn't work everywhere)
find distdevide -name *.so | xargs chrpath --delete
# make a tarball
mv distdevide devide
rm -f devide.tar.gz
tar czvf "devide.tar.gz" devide
mv devide distdevide

else

INSTALLER='python g:/build/Installer/Build.py'
$INSTALLER devide.spec
# optionally make an archive
# mv distdevide devide
# zip -rp "devide-win32-`date +%Y%m%d`.zip" devide
# mv devide distdevide

fi
