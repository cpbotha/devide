#!/bin/bash
# $Id: makeHtmlHelp.sh,v 1.1 2004/03/07 02:11:31 cpbotha Exp $

# go to dir containing script
cd `dirname $0`

# nuke output dir to be sure
rm -rf build
mkdir build

if [ `uname` == Linux ]; then
TEX2RTF=''
else
TEX2RTF='f:/apps/Tex2RTF/tex2rtf.exe'
fi

$TEX2RTF devideHelp.tex build/devideHelp -macros devideHelp.ini
rm ../devideHelp.htb
zip ../devideHelp.htb build/*
