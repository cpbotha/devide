# $Id$

"""Mixins that are useful for classes using vtk_kit.

@author: Charl P. Botha <http://cpbotha.net/>
"""

import utils

class vtk_error_info_class:
    def __init__(self):
        self.error = False
        self.object = None
        self.event_name = None
        self.call_data = None

class vtk_error_func_mixin:
    def __init__(self):
        self.vtk_error_info = vtk_error_info_class()
        self.vtk_error_info.error = False

    def add_error_handler(self, vtk_object):
        utils.add_error_handler(vtk_object, self.error_func)

    def check_error(self):
        if self.vtk_error_info.error:
            raise RuntimeError(self.vtk_error_info.call_data)
    
    def error_func(self, vtk_object, event_name, call_data):
        self.vtk_error_info.error = True
        self.vtk_error_info.object = vtk_object
        self.vtk_error_info.event_name = event_name
        self.vtk_error_info.call_data = call_data

