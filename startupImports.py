# startupImports copyright (c) 2003 by Charl P. Botha http://cpbotha.net/
# $Id: startupImports.py,v 1.7 2003/12/18 14:27:46 cpbotha Exp $
# This is called early on to pre-import some of the larger required libraries
# and give progress messages whilst they are imported.

import os
import sys
import wx

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

def doImports(progressMethod=defaultProgressMethod, useInsight=True):
    importList = [('vtk.common', 'Loading VTK Common.'),
                  ('vtk.filtering', 'Loading VTK Filtering.'),
                  ('vtk.io', 'Loading VTK IO.'),
                  ('vtk.imaging', 'Loading VTK Imaging.'),
                  ('vtk.graphics', 'Loading VTK Graphics.'),
                  ('vtk.rendering', 'Loading VTK Rendering.'),
                  ('vtk.hybrid', 'Loading VTK Hybrid.'),
                  ('vtk.patented', 'Loading VTK Patented.'),
                  ('fixitk.vxlNumericsPythonTopLevel', 'Loading VXL Numerics'),
                  ('fixitk.itkCommonPythonTopLevel', 'Loading ITK Common'),
                  ('fixitk.itkBasicFiltersPythonTopLevel',
                   'fixitk.Loading ITK BasicFilters'),
                  ('fixitk.itkNumericsPythonTopLevel', 'Loading ITK Numerics'),
                  ('fixitk.itkAlgorithmsPythonTopLevel', 'Loading ITK Algorithms'),
                  ('fixitk.itkIOPythonTopLevel', 'Loading ITK IO')]

    if not useInsight:
        # remove ITK things from importList
        importList = [i for i in importList if
                      not i[0].startswith('fixitk') and
                      not i[0].startswith('itk') and
                      not i[0].startswith('vxl')]
                  
    percentStep = 95.0 / len(importList)
    currentPercent = 0.0

    for module, message in importList:
        currentPercent += percentStep
        progressMethod(currentPercent, message, noTime=True)
        wx.SafeYield()
        exec('import %s' % (module,))

    # just to make sure about any other symbols
    import vtk
