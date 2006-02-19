# $Id$

"""Mixins that are useful for classes using vtk_kit.

@author: Charl P. Botha <http://cpbotha.net/>
"""

import utils

class VTKErrorInfoClass:
    """Class used to encapsulate error information in the VTKErrorFuncMixin
    mixin class.
    """
    
    def __init__(self):
        self.error = False
        self.object = None
        self.event_name = None
        self.call_data = None

class VTKErrorFuncMixin:
    """Mixin class that can be used by DeVIDE modules that want to do
    error handling for VTK objects.

    To use this, add it as mixin to your DeVIDE module.   For each VTK object
    that you instantiate, call self.add_vtk_error_handler(vtk_object) once.
    Each time that you execute an object, call self.check_vtk_error().  If an
    error has occurred, an exception will be raised with the appropriate VTK
    error message.
    """
    
    def __init__(self):
        pass
    
    def _ensure_vtk_error_info(self):
        """Guard function that's called by all methods of this class to ensure
        the existence of the info instance.  We do it like this so that the
        user of this mixin does not have to call our constructor.
        """
        
        if not hasattr(self, 'vtk_error_info'):
            self.vtk_error_info = VTKErrorInfoClass()
            self.vtk_error_info.error = False

    def add_vtk_error_handler(self, vtk_object):
        """Instrument a vtk_object with an error observer.

        If any such an object experiences an error, the next call to
        check_vtk_error() will raise an exception with the relevant error
        message.

        @param vtk_object: The vtk object instance that should get the error
        observer.
        """
        
        self._ensure_vtk_error_info()
        utils.add_error_handler(vtk_object, self._vtk_error_func)

    def check_vtk_error(self):
        """Check and raise error if relevant.

        This will check for the most recent error in one of the VTK objects
        that you've instrumented with add_vtk_error_handler().  If an error
        occurred, an exception will be raised with the pertinent VTK error
        message.
        """
        
        self._ensure_vtk_error_info()
        if self.vtk_error_info.error:
            # we're going to raise this error, so first we have to reset
            # the error flag, else subsequent executions might think that
            # we're still erroring
            self.vtk_error_info.error = False
            # finally we get to raise
            raise RuntimeError(self.vtk_error_info.call_data)
    
    def _vtk_error_func(self, vtk_object, event_name, call_data):
        """Default observer function used by add_vtk_error_handler().
        """

        self._ensure_vtk_error_info()
        self.vtk_error_info.error = True
        self.vtk_error_info.object = vtk_object
        self.vtk_error_info.event_name = event_name
        self.vtk_error_info.call_data = call_data

