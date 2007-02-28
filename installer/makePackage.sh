#!/bin/sh
# $Id$
# if you want to use your own PyInstaller Build.py, set the full path
# to this in the ENV variable INSTALLER_SCRIPT

# go to the directory that contains makePackage.sh (i.e. devide/installer)
cd `dirname $0`

if [ "$?" -ne "0" ]; then
echo "ERROR: could not change to devide/installer."
exit 1
fi

# nuke all .pyc files (to be sure)
find ../ -name "*.pyc" -exec rm {} \;
# nuke all backup files
find ../ -name "*~" -exec rm {} \;
find ../ -name "#*#" -exec rm {} \;

# run the McMillan Installer
if [ `uname` = Linux ]; then

# this is so that you can stuff this in the environment
if [ -z "$PYINSTALLER_SCRIPT" ]; then
PYINSTALLER_SCRIPT='/home/cpbotha/build/Installer/Build.py'
fi

INSTALLER="python $PYINSTALLER_SCRIPT"

$INSTALLER devide.spec

if [ "$?" -ne "0" ]; then
echo "ERROR: PyInstaller not successfully executed."
exit 1
fi

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

else

# this is so that you can stuff this in the environment
if [ -z "$PYINSTALLER_SCRIPT" ]; then
PYINSTALLER_SCRIPT='c:/build/Installer/Build.py'
fi

# run the installer
INSTALLER="python $PYINSTALLER_SCRIPT"
$INSTALLER devide.spec

# also copy the manifest file to distdevide
# (we are in the installer directory)
cp devide.exe.manifest distdevide/


fi
