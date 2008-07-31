# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

# general requirements:
# * multiple objects (i.e. multiple coloured contours per slice)

# slice segmentation modes:
# * polygon mode
# * freehand drawing
# * 2d levelset

# see design notes on p39 of AM2 moleskine

from module_base import ModuleBase
from module_mixins import IntrospectModuleMixin
import module_utils

class Slicinator(IntrospectModuleMixin, ModuleBase):
    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        # internal variables

        # config variables
        self._config.somevar = 3

        self._view_frame = None
        self._create_view_frame()
        self._bind_events()

        self.view()

        # all modules should toggle this once they have shown their
        # stuff.
        self.view_initialised = True

        self.config_to_logic()
        self.logic_to_config()
        self.config_to_view()


    def _bind_events(self):
        pass

