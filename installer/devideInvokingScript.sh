#!/bin/sh
# Script that is used on *ix installations of devide to invoke the McMillan
# built binary.  This sets up the LD_LIBRARY_PATH correctly, PYTHONPATH is
# already correct.
# $Id$

START_DIR=`pwd`
cd `dirname $0`
BINDIR=`pwd`
export LD_LIBRARY_PATH=$BINDIR:$BINDIR/support:$BINDIR/module_kits/itk_kit/wrapitk/lib:$LD_LIBRARY_PATH
echo "If you see 'cannot handle TLS data' on startup, "
echo "uncomment LD_ASSUME_KERNEL line in the devide/devide script."
#export LD_ASSUME_KERNEL=2.3.98
$BINDIR/devide.bin $*
cd $START_DIR

