#!/bin/sh
# $Id$

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

else

# run the installer
INSTALLER='python c:/build/Installer/Build.py'
$INSTALLER devide.spec

# also copy the manifest file to distdevide
# (we are in the installer directory)
cp devide.exe.manifest distdevide/

# and now use rebase.exe to rebase all the DLLs for faster loading,
# improved memory use and better sharing of DLLs
# see:
# http://www.codeproject.com/dll/RebaseDll.asp
# http://msdn.microsoft.com/library/default.asp?url=/library/en-us/tools/tools/rebase.asp
# http://www.ddj.com/dept/windows/184416922
# http://discuss.fogcreek.com/joelonsoftware3/default.asp?cmd=show&ixPost=97146&ixReplies=7
# http://forums.amd.com/index.php?showtopic=42055
# http://blogs.msdn.com/larryosterman/archive/2004/07/06/174516.aspx
cd distdevide
find -name "*.dll" > dll_list
find -name "*.pyd" >> dll_list
rebase -b 0x60000000 -e 0x1000000 @dll_list -v
cd ..

fi
