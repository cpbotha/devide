#!/bin/bash
# $Id: makePackage.sh,v 1.13 2004/06/21 16:21:10 cpbotha Exp $

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
# rename the binary and create an invoking script
# we only have to set LD_LIBRARY_PATH, PYTHONPATH is correct
mv distdevide/devide distdevide/devide.bin
SCRIPTFILE='distdevide/devide'
cp devideInvokingScript.sh $SCRIPTFILE
chmod +x $SCRIPTFILE
# make a tarball
mv distdevide devide
rm -f devide.tar.bz2
tar cjvf "devide.tar.bz2" devide
mv devide distdevide

else

INSTALLER='python c:/build/Installer/Build.py'
$INSTALLER devide.spec
# optionally make an archive
# mv distdevide devide
# zip -rp "devide-win32-`date +%Y%m%d`.zip" devide
# mv devide distdevide

fi
