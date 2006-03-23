# $Id$

# importing this module shouldn't directly cause other large imports
# do large imports in the init() hook so that you can call back to the
# moduleManager progress handler methods.

"""vtk_kit package driver file.

This performs all initialisation necessary to use VTK from DeVIDE.  Makes
sure that all VTK classes have ErrorEvent handlers that report back to
the moduleManager.

Inserts the following modules in sys.modules: vtk, vtkdevide.

@author: Charl P. Botha <http://cpbotha.net/>
"""

import re
import sys
import types

VERSION = ''
VTK_VERSION_EXTRA = '-r VTK-5-0'

def preImportVTK(progressMethod):
    vtkImportList = [('vtk.common', 'VTK Common.'),
                     ('vtk.filtering', 'VTK Filtering.'),
                     ('vtk.io', 'VTK IO.'),
                     ('vtk.imaging', 'VTK Imaging.'),
                     ('vtk.graphics', 'VTK Graphics.'),
                     ('vtk.rendering', 'VTK Rendering.'),
                     ('vtk.hybrid', 'VTK Hybrid.'),
                     #('vtk.patented', 'VTK Patented.'),
                     ('vtk', 'Other VTK symbols')]

    # set the dynamic loading flags.  If we don't do this, we get strange
    # errors on 64 bit machines.  To see this happen, comment this statement
    # and then run the VTK->ITK connection test case.
    oldflags = setDLFlags()

    percentStep = 100.0 / len(vtkImportList)
    currentPercent = 0.0

    # do the imports
    for module, message in vtkImportList:
        currentPercent += percentStep
        progressMethod(currentPercent, 'Initialising vtk_kit: %s' % (message,),
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
    preImportVTK(theModuleManager.setProgress)

    # import the main module itself
    # the global is so that users can also do:
    # from module_kits import vtk_kit
    # vtk_kit.vtk.vtkSomeFilter()
    global vtk
    import vtk

    # and do the same for vtkdevide
    global vtkdevide
    import vtkdevide

    # setup some default error handling for VTK objects that have neither
    # ErrorEvent or WarningEvent observers

    def observer_eow_error(o, e):
        theModuleManager.log_error(o.GetText())

    def observer_eow_warning(o, e):
        theModuleManager.log_warning(o.GetText())
    
    eow = vtkdevide.vtkEventOutputWindow()
    eow.AddObserver('ErrorEvent', observer_eow_error)
    eow.AddObserver('WarningEvent', observer_eow_warning)
    
    eow.SetInstance(eow)

    # load up some generic functions into this namespace
    # user can, after import of module_kits.vtk_kit, address these as
    # module_kits.vtk_kit.blaat.  In this case we don't need "global",
    # as these are modules directly in this package.
    import module_kits.vtk_kit.misc as misc
    import module_kits.vtk_kit.mixins as mixins
    import module_kits.vtk_kit.utils as utils

    # setup the kit version
    global VERSION

    # moo
    vsv = vtk.vtkVersion.GetVTKSourceVersion()
    # VTK source nightly date
    vnd = re.match('.*Date: ([0-9]+/[0-9]+/[0-9]+).*', vsv).group(1)
    VERSION = '%s (%s: %s)' % (vtk.vtkVersion.GetVTKVersion(), vnd,
                               VTK_VERSION_EXTRA)
    
