#!/bin/sh
# $Id: makeRelease.sh,v 1.7 2005/01/12 22:49:14 cpbotha Exp $
# makeRelease for devide copyright 2004 Charl P. Botha http://cpbotha.net/

# script to build a complete release:
# 1. cvs updates on devide and vtkdevide
# 2. configure and build vtkdevide
# 3. make documentation (help)
# 4. run package building script (makePackage.sh) to
#    make normal and optionally ITK-release
#    (depending on switch)
# 5. also run makensis on Windows to build the installer

# extra requirements: cygwin/mingw (we need sh, sed, uname, date)
#                     zip (from info-zip)
#                     NSIS installer 2.0 or later
# parameter(s): "sh makeRelease noitk" won't build itk binaries.

# TODO: rewrite in Python damnit!

# go to the directory that contains makePackage.sh (i.e. devide/installer)
cd `dirname $0`

# make sure all our dependencies are up to date
# first change to the dir containing the correct script (devide/utils)
cd ../utils
# then use our python script to make sure all is up to date
if [ "$1" != noitk ]; then
python updateAll.py
else
python updateAll.py --no-itk
fi
# go back to the devide dir
cd ../

# make documentation
echo "Building documentation..."
cd docs/help/source
sh ./makeHtmlHelp.sh
cd ../../../

# now make VTK and ITK version
echo "Building VTK version..."

cp defaults.py defaults.py.backup
cat defaults.py | sed -e 's/USE_INSIGHT *= *.*/USE_INSIGHT = False/g' > defaultsTemp.py
cp defaultsTemp.py defaults.py

cd installer
sh ./makePackage.sh
if [ `uname` != Linux ]; then
c:/Program\ Files/NSIS/makensis.exe devide.nsi
cp devidesetup.exe devidesetup`date +%Y%m%d`.exe
else
cp devide.tar.bz2 devide`date +%Y%m%d`.tar.bz2
fi

cd ../
cp defaults.py.backup defaults.py
rm defaults.py.backup defaultsTemp.py

# unless the user has instructed us NOT to build ITK, do it
if [ "$1" != noitk ]; then
echo "Building ITK version..."

cp defaults.py defaults.py.backup
cat defaults.py | sed -e 's/USE_INSIGHT *= *.*/USE_INSIGHT = True/g' > defaultsTemp.py
cp defaultsTemp.py defaults.py

cd installer
sh ./makePackage.sh
if [ `uname` != Linux ]; then
c:/Program\ Files/NSIS/makensis.exe devide.nsi
cp devidesetup.exe devidesetup`date +%Y%m%d`itk.exe
else
cp devide.tar.bz2 devide`date +%Y%m%d`itk.tar.bz2
fi

cd ../
cp defaults.py.backup defaults.py
rm defaults.py.backup defaultsTemp.py
fi
