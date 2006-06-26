# $Id$

"""itk_kit package driver file.

Inserts the following modules in sys.modules: itk, InsightToolkit.

@author: Charl P. Botha <http://cpbotha.net/>
"""

import re
import sys

VERSION = ''
ITK_VERSION_EXTRA = '-r ITK-2-8'

def preImportITK(progressMethod):
    itkImportList = [('VXLNumericsPython', 'VXL Numerics'),
                     ('ITKCommonAPython', 'ITK Common part A'),
                     ('ITKCommonBPython', 'ITK Common part B'),
                     ('ITKBasicFiltersAPython', 'ITK Basic Filters A'),
                     ('ITKBasicFiltersBPython', 'ITK Basic Filters B'),
                     ('ITKNumericsPython', 'ITK Numerics'),
                     ('ITKAlgorithmsPython', 'ITK Algorithms'),
                     ('ITKIOPython', 'ITK IO Python'),
                     ('fixitk', 'Other ITK symbols')] # fixitk
    

    # set the dynamic loading flags.  If we don't do this, we get strange
    # errors on 64 bit machines.  To see this happen, comment this statement
    # and then run the VTK->ITK connection test case.
    oldflags = setDLFlags()

    percentStep = 100.0 / len(itkImportList)
    currentPercent = 0.0

    # do the imports
    for module, message in itkImportList:
        currentPercent += percentStep
        progressMethod(currentPercent, 'Initialising itk_kit: %s' % (message,),
                       noTime=True)
        exec('import %s' % (module,))

    # restore previous dynamic loading flags
    resetDLFlags(oldflags)

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

def init(theModuleManager):

    # with WrapITK, this takes almost no time
    import itk

    theModuleManager.setProgress(5, 'Initialising ITK: start')

    # let's get the version (which will bring in VXLNumerics and Base)

    # setup the kit version
    global VERSION
    isv = itk.Version.GetITKSourceVersion()
    ind = re.match('.*Date: ([0-9]+/[0-9]+/[0-9]+).*', isv).group(1)
    VERSION = '%s (%s: %s)' % (itk.Version.GetITKVersion(), ind,
                               ITK_VERSION_EXTRA)

    theModuleManager.setProgress(45, 'Initialising ITK: VXLNumerics, Base')

    # then ItkVtkGlue (at the moment this is fine, VTK is always there;
    # keep in mind for later when we allow VTK-less startups)
    a = itk.VTKImageToImageFilter

    theModuleManager.setProgress(
        75,
        'Initialising ITK: BaseTransforms, SimpleFilters, ItkVtkGlue')
    
    # user can address this as module_kits.itk_kit.utils.blaat()
    import module_kits.itk_kit.utils as utils

    theModuleManager.setProgress(100, 'Initialising ITK: DONE')


