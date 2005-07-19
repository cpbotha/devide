# startupImports copyright (c) 2003 by Charl P. Botha http://cpbotha.net/
# $Id: startupImports.py,v 1.13 2005/07/19 14:45:48 cpbotha Exp $
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
except SystemError:
    # this covers us on RHEL3 64 for:
    # SysError: module dl requires sizeof(int) == sizeof(long) == sizeof(char*) 
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


def setDLFlags():
    # brought over from ITK Wrapping/CSwig/Python

    # Python "help(sys.setdlopenflags)" states:
    #
    # setdlopenflags(...)
    #     setdlopenflags(n) -> None
    #     
    #     Set the flags that will be used for dlopen() calls. Among other
    #     things, this will enable a lazy resolving of symbols when
    #     importing a module, if called as sys.setdlopenflags(0) To share
    #     symbols across extension modules, call as
    #
    #     sys.setdlopenflags(dl.RTLD_NOW|dl.RTLD_GLOBAL)
    #
    # GCC 3.x depends on proper merging of symbols for RTTI:
    #   http://gcc.gnu.org/faq.html#dso
    #
    try:
        import dl
        newflags = dl.RTLD_NOW|dl.RTLD_GLOBAL
    except:
        newflags = 0x102  # No dl module, so guess (see above).
        
    try:
        oldflags = sys.getdlopenflags()
        sys.setdlopenflags(newflags)
    except:
        oldflags = None

    return oldflags

def resetDLFlags(data):
    # brought over from ITK Wrapping/CSwig/Python    
    # Restore the original dlopen flags.
    try:
        sys.setdlopenflags(data)
    except:
        pass
    

def doImports(progressMethod, mainConfig):
    vtkImportList = [('vtk.common', 'Loading VTK Common.'),
                     ('vtk.filtering', 'Loading VTK Filtering.'),
                     ('vtk.io', 'Loading VTK IO.'),
                     ('vtk.imaging', 'Loading VTK Imaging.'),
                     ('vtk.graphics', 'Loading VTK Graphics.'),
                     ('vtk.rendering', 'Loading VTK Rendering.'),
                     ('vtk.hybrid', 'Loading VTK Hybrid.'),
                     #('vtk.patented', 'Loading VTK Patented.'),
                     ('vtk', 'Loading other VTK symbols')]

    itkImportList = [('VXLNumericsPython', 'Loading VXL Numerics'),
                     ('ITKCommonAPython', 'Loading ITK Common part A'),
                     ('ITKCommonBPython', 'Loading ITK Common part B'),
                     ('ITKBasicFiltersAPython', 'Loading ITK Basic Filters A'),
                     ('ITKBasicFiltersBPython', 'Loading ITK Basic Filters B'),
                     ('ITKNumericsPython', 'Loading ITK Numerics'),
                     ('ITKAlgorithmsPython', 'Loading ITK Algorithms'),
                     ('ITKIOPython', 'Loading ITK IO Python'),
                     ('fixitk', 'Loading other ITK symbols')]

    # set the dynamic loading flags.  If we don't do this, we get strange
    # errors on 64 bit machines.  To see this happen, comment this statement
    # and then run the VTK->ITK connection test case.
    oldflags = setDLFlags()

    # set up list of modules to import
    importList = vtkImportList

    if mainConfig.useInsight and mainConfig.itkPreImport:
        importList += itkImportList
                  
    percentStep = 95.0 / len(importList)
    currentPercent = 0.0

    # do the imports
    for module, message in importList:
        currentPercent += percentStep
        progressMethod(currentPercent, message, noTime=True)
        wx.SafeYield()
        exec('import %s' % (module,))

    # restore previous dynamic loading flags
    resetDLFlags(oldflags)
