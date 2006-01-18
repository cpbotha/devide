# $Id$

"""Utility methods for vtkKit module kit.

@author Charl P. Botha <http://cpbotha.net/>
"""

class error_event_class:
    """Class used to encapsulate error_func with error_event_handler.
    """
    
    def __init__(self, error_func):
        self.error_func = error_func
        
    def error_event_handler(self, vtk_object, event_name, call_data):
        """Standard error handler for VTK objects that can be used by vtkKit
        dependent DeVIDE modules.
        """

        ef = self.error_func
        ef(vtk_object, event_name, call_data)

    error_event_handler.CallDataType = "string0"

def add_error_handler(vtk_object, error_func):
    """Add standard error handler to a vtk object.

    The error handler will be added as an observer to the given vtk_object.
    No exceptions can be raised inside the error handler, but a variable of
    your choice can be toggled to indicate that an error has occurred.

    @param vtk_object: the vtk object to which the error handler should be
    added.
    @param error_func: this function will be called with vtk_object,
    event_name and call_data as parameters.
    """

    eec = error_event_class(error_func)
    vtk_object.AddObserver('ErrorEvent', eec.error_event_handler)

