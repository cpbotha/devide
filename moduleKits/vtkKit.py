import types
import sys

def ErrorEventHandler(theObject, eventName, callData):
    # due to the VTK Python wrappings, raising an exception here will
    # only print the error, not go through the complete exceptiong handling
    # trajectory - best we can do is to toggle some error flag somewhere
    # and react on it later
    print "YEEEHAAAAW!  Error trapped: %s" % (callData,)

ErrorEventHandler.CallDataType = "string0"

class vtkModuleTrappedErrors(types.ModuleType):
    """Class to enable default instantiation of all wrapped VTK classes with
    ErrorEvent observers.

    @author: Charl P. Botha <http://cpbotha.net/>
    """
    
    def __getattribute__(self, name):
        if name.startswith('vtk'):
            klass = object.__getattribute__(self, name)
            class vtkClassTrappedErrors(klass):
                def __init__(self):
                    # if our base class has a ctor, call it
                    try:
                        rv = klass.__init__(self)
                    except AttributeError, e:
                        rv = None

                    if hasattr(self, 'AddObserver'):
                        # add the ErrorEvent observer
                        self.AddObserver('ErrorEvent', ErrorEventHandler)

                    # in the case of a vtkAlgorithm, the Executive has to
                    # be instrumented as well
                    if hasattr(self, 'GetExecutive'):
                        self.GetExecutive().AddObserver(
                            'ErrorEvent', ErrorEventHandler)
                    
                    # and return either the value of the parent constructor
                    # or none if there was no parent.
                    return rv

            # return our instrumented class instead of the native vtkclass
            return vtkClassTrappedErrors
        
        else:
            # for everything else, thunk back to the default
            return object.__getattribute__(self, name)

def init(theModuleManager):
    # finally import VTK by first instantiating our new ModuleType class
    vtk = vtkModuleTrappedErrors('vtk')
    # installing it in the modules directory
    sys.modules['vtk'] = vtk
    # and then requesting a reload
    reload(vtk)

