# startupImports copyright (c) 2003 by Charl P. Botha http://cpbotha.net/
# $Id: startupImports.py,v 1.1 2003/08/11 16:49:42 cpbotha Exp $
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
    steps = 8
    percentStep = 95.0 / steps
    currentPercent = 0.0

    importList = [('vtk.common', 'Importing VTK Common'),
                  ('vtk.filtering', 'Importing VTK Filtering')]
                  
    currentPercent += percentStep
    progressMethod(currentPercent, "Importing VTK Common.")
    wx.SafeYield()
    import vtk.common

    currentPercent += percentStep
    progressMethod(currentPercent, "Importing VTK Filtering.")
    wx.SafeYield()
    import vtk.filtering

    currentPercent += percentStep
    progressMethod(currentPercent, "Importing VTK IO.")
    wx.SafeYield()
    import vtk.io
    
    currentPercent += percentStep
    progressMethod(currentPercent, "Importing VTK Imaging.")
    wx.SafeYield()
    import vtk.imaging

    currentPercent += percentStep
    progressMethod(currentPercent, "Importing VTK Graphics.")
    wx.SafeYield()
    import vtk.graphics

    currentPercent += percentStep
    progressMethod(currentPercent, "Importing VTK Rendering.")
    wx.SafeYield()
    import vtk.rendering

    currentPercent += percentStep
    progressMethod(currentPercent, "Importing VTK Hybrid.")
    wx.SafeYield()
    import vtk.patented

    # just to make sure about any other symbols
    import vtk
