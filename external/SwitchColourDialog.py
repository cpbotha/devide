# $Id$
#
# This very simple module enables one to make use of a "ColourDialog" class
# which on Windows maps to the native wxColourDialog and on all other
# platforms to the PyColourChooserDialog (by me) which in turn makes use
# of the pycolourchooser module by Michael Gilfix.
#
# This code is distributed under the conditions of the BSD license.
# See LICENSE.txt for details.
#
# Copyright (c) 2003 Charl P. Botha
#
# This software is distributed WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the above copyright notice for more information.
#
# Author contact information:
#   Charl P. Botha <cpbotha@ieee.org>
#   http://cpbotha.net/

import wx
import sys

if sys.platform.startswith('win'):
    ColourDialog = wx.ColourDialog
else:
    import PyColourChooserDialog
    ColourDialog = PyColourChooserDialog.PyColourChooserDialog


