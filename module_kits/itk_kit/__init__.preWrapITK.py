# $Id: __init__.py 1967 2006-03-08 00:26:38Z cpbotha $

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
    # first do the VTK pre-imports: this is here ONLY to keep the user happy
    # it's not necessary for normal functioning
    preImportITK(theModuleManager.setProgress)

    # brings 'InsightToolkit' into sys.modules
    import fixitk as itk
    # stuff itk in there as well (so that if the user does import itk,
    # she'll get this)
    sys.modules['itk'] = itk

    # user can address this as module_kits.itk_kit.utils.blaat()
    import module_kits.itk_kit.utils as utils

    # also import the VTK to ITK connection module
    import ConnectVTKITKPython as CVIPy

    # setup the kit version
    global VERSION

    # let's hope McMillan doesn't catch this one!
    isv = itk.itkVersion.GetITKSourceVersion()
    ind = re.match('.*Date: ([0-9]+/[0-9]+/[0-9]+).*', isv).group(1)
    VERSION = '%s (%s: %s)' % (itk.itkVersion.GetITKVersion(), ind,
                               ITK_VERSION_EXTRA)
