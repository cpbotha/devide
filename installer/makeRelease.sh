#!/bin/bash
# $Id: makeRelease.sh,v 1.2 2004/03/20 18:14:01 cpbotha Exp $
# makeRelease for devide copyright 2004 Charl P. Botha http://cpbotha.net/

# script to build a complete release:
# 1. cvs updates on devide and vtkdevide
# 2. configure and build vtkdevide
# 3. make documentation (help)
# 4. run package building script (makePackage.sh) to
#    make normal and optionally ITK-release
#    (depending on switch)
# 5. also run makensis on Windows to build the installer

# requirements: cygwin (we need bash, sed, uname, date)
# parameter(s): "bash makeRelease noitk" won't build itk binaries.
# TODO: rewrite in Python damnit!

# go to the directory that contains makePackage.sh (i.e. devide/installer)
cd `dirname $0`

# make sure devide and vtkdevide sources are up to date
echo "Updating devide and vtkdevide sources..."
cd ..
cvs update -dAP
cd ../vtkdevide
cvs update -dAP

# make sure vtkdevide is up to date, conf and build
echo "Building vtkdevide..."
cmake .
if [ `uname` == Linux ]; then
make
else
./msBuild.bat
fi
cd ../devide

# make documentation
echo "Building documentation..."
cd docs/help/source
bash ./makeHtmlHelp.sh
cd ../../../

# now make VTK and ITK version
echo "Building VTK version..."

cp defaults.py defaults.py.backup
cat defaults.py | sed -e 's/USE_INSIGHT *= *.*/USE_INSIGHT = False/g' > defaultsTemp.py
cp defaultsTemp.py defaults.py

cd installer
bash ./makePackage.sh
if [ `uname` != Linux ]; then
f:/Program\ Files/NSIS/makensis.exe devide.nsi
cp devidesetup.exe devidesetup`date +%Y%m%d`.exe
else
cp devide.tar.gz devide`date +%Y%m%d`.tar.gz
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
bash ./makePackage.sh
if [ `uname` != Linux ]; then
f:/Program\ Files/NSIS/makensis.exe devide.nsi
cp devidesetup.exe devidesetup`date +%Y%m%d`itk.exe
else
cp devide.tar.gz devide`date +%Y%m%d`itk.tar.gz
fi

cd ../
cp defaults.py.backup defaults.py
rm defaults.py.backup defaultsTemp.py
fi
