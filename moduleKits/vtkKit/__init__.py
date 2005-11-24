# $Id: __init__.py,v 1.5 2005/11/24 13:12:31 cpbotha Exp $

# importing this module shouldn't directly cause other large imports
# do large imports in the init() hook so that you can call back to the
# moduleManager progress handler methods.

"""vtkKit package driver file.

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
VTK_VERSION_EXTRA = '-D'

class vtkModuleTrappedErrors(types.ModuleType):
    """Class to enable default instantiation of all wrapped VTK classes with
    ErrorEvent observers.

    @author: Charl P. Botha <http://cpbotha.net/>
    """

    def __init__(self, name, moduleManager):
        types.ModuleType.__init__(self, name)
        self._moduleManager = moduleManager
        
    def ErrorEventHandler(self, theObject, eventName, callData):
        """Standard handler for DeVIDE vtkKit object ErrorEvents.

        Due to the Python wrappings, an exception raised here will not
        go through the normal catch handling, but will instead just
        be printed to stdout.  Instead, we use moduleManager functionality
        to indicate the error.  moduleManager will trap these errors
        and handle them as it usually does.
        """

        # we only have to report the specific VTK object error,
        # moduleManager will add information about which DeVIDE module
        # contains the error
        self._moduleManager.addNoExcModuleExecError(callData)
        # debug output
        print callData

    ErrorEventHandler.CallDataType = "string0"
    
    def __getattribute__(self, name):
        if name.startswith('vtk'):
            klass = object.__getattribute__(self, name)
            
            # dynamically-created class to wrap vtk_object ##################
            class vtkClassTrappedErrors(klass):
                def __init__(zelf):
                    # if our base class has a ctor, call it
                    try:
                        rv = klass.__init__(zelf)
                    except AttributeError, e:
                        rv = None

                    if hasattr(zelf, 'AddObserver'):
                        # add the ErrorEvent observer
                        zelf.AddObserver(
                            'ErrorEvent', self.ErrorEventHandler)

                    # in the case of a vtkAlgorithm, the Executive has to
                    # be instrumented as well
                    if hasattr(zelf, 'GetExecutive'):
                        zelf.GetExecutive().AddObserver(
                            'ErrorEvent', self.ErrorEventHandler)
                    
                    # and return either the value of the parent constructor
                    # or none if there was no parent.
                    return rv

            # end of dynamically-created class ############################

            # return our instrumented class instead of the native vtkclass
            return vtkClassTrappedErrors
        
        else:
            # for everything else, thunk back to the default
            return object.__getattribute__(self, name)

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
        progressMethod(currentPercent, 'Initialising vtkKit: %s' % (message,),
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
    
    # finally import VTK by first instantiating our new ModuleType class
    vtk = vtkModuleTrappedErrors('vtk', theModuleManager)
    # installing it in the modules directory
    sys.modules['vtk'] = vtk
    # and then requesting a reload
    reload(vtk)

    # and do the same for vtkdevide, vtktud
    vtkdevide = vtkModuleTrappedErrors('vtkdevide', theModuleManager)
    sys.modules['vtkdevide'] = vtkdevide
    reload(vtkdevide)

    # load up some generic functions into this namespace
    import misc

    # setup the kit version
    global VERSION

    # moo
    vsv = vtk.vtkVersion.GetVTKSourceVersion()
    # VTK source nightly date
    vnd = re.match('.*Date: ([0-9]+/[0-9]+/[0-9]+).*', vsv).group(1)
    VERSION = '%s (%s: %s)' % (vtk.vtkVersion.GetVTKVersion(), vnd,
                               VTK_VERSION_EXTRA)
    
