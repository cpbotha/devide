# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

import os
from module_base import ModuleBase
from module_mixins import IntrospectModuleMixin,\
        FileOpenDialogModuleMixin
import module_utils
import vtk
import wx

STATE_INIT = 0


class LarynxMeasurement(IntrospectModuleMixin, FileOpenDialogModuleMixin, ModuleBase):

    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        self._state = STATE_INIT

        self._view_frame = None
        self._viewer = None
        self._reader = vtk.vtkJPEGReader()
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
        self._view_frame.start_button.Bind(
                wx.EVT_BUTTON, self._handler_start_button)
        

    def _create_view_frame(self):
        import resources.python.larynx_measurement_frame
        reload(resources.python.larynx_measurement_frame)

        self._view_frame = module_utils.instantiate_module_view_frame(
            self, self._module_manager,
            resources.python.larynx_measurement_frame.LarynxMeasurementFrame)

        module_utils.create_standard_object_introspection(
            self, self._view_frame, self._view_frame.view_frame_panel,
            {'Module (self)' : self})

        # add the ECASH buttons
        #module_utils.create_eoca_buttons(self, self._view_frame,
        #                                self._view_frame.view_frame_panel)


        # now setup the VTK stuff
        if self._viewer is None and not self._view_frame is None:
            self._viewer = vtk.vtkImageViewer2()
            self._viewer.SetupInteractor(self._view_frame.rwi)
            self._viewer.GetRenderer().SetBackground(0.3,0.3,0.3)
            self._set_image_viewer_dummy_input()
    


    def close(self):
        for i in range(len(self.get_input_descriptions())):
            self.set_input(i, None)

        # with this complicated de-init, we make sure that VTK is 
        # properly taken care of
        self._viewer.GetRenderer().RemoveAllViewProps()
        self._viewer.SetupInteractor(None)
        self._viewer.SetRenderer(None)
        # this finalize makes sure we don't get any strange X
        # errors when we kill the module.
        self._viewer.GetRenderWindow().Finalize()
        self._viewer.SetRenderWindow(None)
        del self._viewer
        # done with VTK de-init

       
        self._view_frame.Destroy()
        del self._view_frame

        ModuleBase.close(self)

    def get_input_descriptions(self):
        return ()

    def get_output_descriptions(self):
        return ()

    def set_input(self, idx, input_stream):
        raise RuntimeError

    def get_output(self, idx):
        raise RuntimeError

    def logic_to_config(self):
        pass

    def config_to_logic(self):
        pass

    def view_to_config(self):
        pass

    def config_to_view(self):
        pass

    def view(self):
        self._view_frame.Show()
        self._view_frame.Raise()

        # we need to do this to make sure that the Show() and Raise() above
        # are actually performed.  Not doing this is what resulted in the
        # "empty renderwindow" bug after module reloading, and also in the
        # fact that shortly after module creation dummy data rendered outside
        # the module frame.
        wx.SafeYield()

        self.render()
        # so if we bring up the view after having executed the network once,
        # re-executing will not do a set_input()!  (the scheduler doesn't
        # know that the module is now dirty)  Two solutions:
        # * make module dirty when view is activated
        # * activate view at instantiation. <--- we're doing this now.
 
    def execute_module(self):
        pass


    def _handler_start_button(self, evt):
        # let user pick image
        # - close down any running analysis
        # - analyze all jpg images in that dir
        # - read / initialise SQL db

        # first get filename from user
        filename = self.filename_browse(self._view_frame, 
        'Select FIRST subject image to start processing', 
        'Subject image (*.jpg)|*.jpg;*.JPG', 
        style=wx.OPEN)

        if filename:
            # create a new instance of the current reader
            # to check that we can read this file
            nr = self._reader.NewInstance()
            nr.SetFileName(filename)
            # FIXME: trap this error
            nr.Update()

            self._stop()
            self._start(nr)

    def render(self):
        self._viewer.Render()

    def _stop(self):
        # close down any running analysis
        pass

    def _start(self, new_reader):
        self._reader = new_reader
        self._viewer.SetInput(self._reader.GetOutput())
        self.render()

        
    def _set_image_viewer_dummy_input(self):
        ds = vtk.vtkImageGridSource()
        self._viewer.SetInput(ds.GetOutput())


