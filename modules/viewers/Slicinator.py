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
        self._create_vtk_pipeline()

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
        import resources.python.slicinator_frames
        reload(resources.python.slicinator_frames)

        self._view_frame = module_utils.instantiate_module_view_frame(
            self, self._module_manager,
            resources.python.slicinator_frames.SlicinatorFrame)

        vf = self._view_frame

    def _create_vtk_pipeline(self):
        vf = self._view_frame

        # create the necessary VTK objects: we only need a renderer,
        # the RenderWindowInteractor in the view_frame has the rest.
        self.ren = vtk.vtkRenderer()
        self.ren.SetBackground(0.5,0.5,0.5)
        self._view_frame.rwi.GetRenderWindow().AddRenderer(self.ren)

    def close(self):
        # with this complicated de-init, we make sure that VTK is 
        # properly taken care of
        self.ren.RemoveAllViewProps()
        # this finalize makes sure we don't get any strange X
        # errors when we kill the module.
        self._view_frame.rwi.GetRenderWindow().Finalize()
        self._view_frame.rwi.SetRenderWindow(None)
        del self._view_frame.rwi
        # done with VTK de-init
       
        self._view_frame.Destroy()
        del self._view_frame

        IntrospectModuleMixin.close(self)
        ModuleBase.close(self)

    def execute_module(self):
        pass

    def get_input_descriptions(self):
        return ()

    def get_output_descriptions(self):
        return ()

    def logic_to_config(self):
        pass

    def config_to_logic(self):
        pass

    def config_to_view(self):
        pass

    def view_to_config(self):
        pass


    def view(self):
        self._view_frame.Show()
        self._view_frame.Raise()




    


