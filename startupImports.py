# startupImports copyright (c) 2003 by Charl P. Botha http://cpbotha.net/
# $Id: startupImports.py,v 1.2 2003/08/27 12:34:36 cpbotha Exp $
# This is called early on to pre-import some of the larger required libraries
# and give progress messages whilst they are imported.


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
    print "%3.2f - %s" % (percentage, message)

def doImports(progressMethod=defaultProgressMethod):
    importList = [('vtk.common', 'Importing VTK Common.'),
                  ('vtk.filtering', 'Importing VTK Filtering.'),
                  ('vtk.io', 'Importing VTK IO.'),
                  ('vtk.imaging', 'Importing VTK Imaging.'),
                  ('vtk.graphics', 'Importing VTK Graphics.'),
                  ('vtk.rendering', 'Importing VTK Rendering.'),
                  ('vtk.hybrid', 'Importing VTK Hybrid.'),
                  ('vtk.patented', 'Importing VTK Patented.')]
                  
    percentStep = 95.0 / len(importList)
    currentPercent = 0.0
                  
    for module, message in importList:
        currentPercent += percentStep
        progressMethod(currentPercent, message)
        wx.SafeYield()
        exec('import %s' % (module,))

    # just to make sure about any other symbols
    import vtk
