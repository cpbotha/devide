#!/bin/bash
# $Id$

# go to dir containing script
cd `dirname $0`

# nuke output dir to be sure
rm -rf build
mkdir build

if [ `uname` == Linux ]; then
TEX2RTF='tex2rtf'
else
TEX2RTF='tex2rtf.exe'
fi

$TEX2RTF devideHelp.tex build/devidehelp -macros devideHelp.ini
# now copy figures
cp figures/* build

# devideHelp.htb is in appDir/docs/help/
# this script is in appDir/docs/help/source
rm ../devideHelp.htb
cd build
zip ../../devideHelp.htb *


