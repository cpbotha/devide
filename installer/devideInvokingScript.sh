#!/bin/sh
# Script that is used on *ix installations of devide to invoke the McMillan
# built binary.  This sets up the LD_LIBRARY_PATH correctly, PYTHONPATH is
# already correct.
# $Id: devideInvokingScript.sh,v 1.2 2004/06/21 16:30:25 cpbotha Exp $

START_DIR=`pwd`
cd `dirname $0`
BINDIR=`pwd`
export LD_LIBRARY_PATH=$BINDIR/support:$LD_LIBRARY_PATH
$BINDIR/devide.bin $*
cd $START_DIR
