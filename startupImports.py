# startupImports copyright (c) 2003 by Charl P. Botha http://cpbotha.net/
# $Id: startupImports.py,v 1.5 2003/10/15 22:02:15 cpbotha Exp $
# This is called early on to pre-import some of the larger required libraries
# and give progress messages whilst they are imported.

# NB: also see installer/hooks/hook-startupImports.py !

# we also pre-import as much as possible of wxPython to make sure that the
# weird-assed wx renamer doesn't get to us.  The hook for this module also
# goes to some trouble to prevent the wx-renamer from biting our ass later.
from wxPython.wx import *
from wxPython.html import *
from wxPython.lib import *
from wxPython.py import *

# we're safe now due to all that crazy importing.  I hope.
import wx

import os
import sys

# AIX apparently does not have dl?
try:
    import dl
except ImportError:
    dl = None

#import __helper

# set the dlopen flags so that VTK does not run into problems with
# shared symbols.
try:
    # only Python >= 2.2 has this functionality
    orig_dlopen_flags = sys.getdlopenflags()
except AttributeError:
    orig_dlopen_flags = None

if dl and (os.name == 'posix'):
    sys.setdlopenflags(dl.RTLD_NOW|dl.RTLD_GLOBAL)

def defaultProgressMethod(percentage, message):
    print "%s [%3.2f]" % (message, percentage)

def doImports(progressMethod=defaultProgressMethod):
    importList = [('vtk.common', ' VTK Common.'),
                  ('vtk.filtering', ' VTK Filtering.'),
                  ('vtk.io', ' VTK IO.'),
                  ('vtk.imaging', ' VTK Imaging.'),
                  ('vtk.graphics', ' VTK Graphics.'),
                  ('vtk.rendering', ' VTK Rendering.'),
                  ('vtk.hybrid', ' VTK Hybrid.'),
                  ('vtk.patented', ' VTK Patented.')]
                  
    percentStep = 95.0 / len(importList)
    currentPercent = 0.0

    progressMethod(0.0, 'Preloading VTK libraries...')
    
    for module, message in importList:
        currentPercent += percentStep
        progressMethod(currentPercent, message)
        wx.SafeYield()
        exec('import %s' % (module,))

    # just to make sure about any other symbols
    import vtk
