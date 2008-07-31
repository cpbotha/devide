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

    def _create_view_frame(self):
        import resources.python.slicinator_frame
        reload(resources.python.slicinator_frame

        self._view_frame = module_utils.instantiate_module_view_frame(
            self, self._module_manager,
            resources.python.slicinator_frame.SlicinatorFrame)

        module_utils.create_standard_object_introspection(
            self, self._view_frame, self._view_frame.view_frame_panel,
            {'Module (self)' : self})

        # add the ECASH buttons
        module_utils.create_eoca_buttons(self, self._view_frame,
                                        self._view_frame.view_frame_panel)

        # and customize the presets choice
        vf = self._view_frame
        keys = TF_LIBRARY.keys()
        keys.sort()
        vf.preset_choice.Clear()
        for key in keys:
            vf.preset_choice.Append(key)

        vf.preset_choice.Select(0)

