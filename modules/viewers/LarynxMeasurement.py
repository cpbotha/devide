# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

import os
from module_base import ModuleBase
from module_mixins import IntrospectModuleMixin,\
        FileOpenDialogModuleMixin
import module_utils
import vtk
import vtkgdcm
import wx

STATE_INIT = 0
STATE_IMAGE_LOADED = 1


class LarynxMeasurement(IntrospectModuleMixin, FileOpenDialogModuleMixin, ModuleBase):

    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        self._state = STATE_INIT
        self._config.filename = None

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

        self._view_frame.rwi.AddObserver(
                'LeftButtonPressEvent',
                self._handler_rwi_lbp)
        

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
            # vtkImageViewer() does not zoom but retains colour
            # vtkImageViewer2() does zoom but discards colour at
            # first window-level action.
            # vtkgdcm.vtkImageColorViewer() does both right!
            self._viewer = vtkgdcm.vtkImageColorViewer()
            self._viewer.SetupInteractor(self._view_frame.rwi)
            self._viewer.GetRenderer().SetBackground(0.3,0.3,0.3)
            self._set_image_viewer_dummy_input()

            pp = vtk.vtkPointPicker()
            pp.SetTolerance(0.0)
            self._view_frame.rwi.SetPicker(pp)
    


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
        # there is no explicit apply step in this viewer module, so we
        # keep the config up to date throughout (this is common for
        # pure viewer modules)
        pass

    def config_to_view(self):
        # this will happen right after module reload / network load
        if self._config.filename is not None:
            self._start(self._config.filename)


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

    def _handler_rwi_lbp(self, vtk_o, vtk_e):
        pp = vtk_o.GetPicker() # this will be our pointpicker
        x,y = vtk_o.GetEventPosition()
        if not pp.Pick(x,y,0,self._viewer.GetRenderer()):
            print "off image!"
        else:
            print pp.GetMapperPosition()
        
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
            self._start(filename)

    def render(self):
        self._viewer.Render()

    def _reset_image_pz(self):
        """Reset the pan/zoom of the current image.
        """

        ren = self._viewer.GetRenderer()
        ren.ResetCamera()

    def _stop(self):
        # close down any running analysis
        self._set_image_viewer_dummy_input()
        self._state = STATE_INIT

    def _start(self, new_filename):
        # first see if we can open the new file
        new_reader = self._open_image_file(new_filename)
        # FIXME: also check if we can open / create sqlite file

        # if so, stop previous session
        self._stop()

        # replace reader and show the image
        self._reader = new_reader
        self._viewer.SetInput(self._reader.GetOutput())

        # show the new filename in the correct image box
        self._view_frame.current_image_txt.SetValue(new_filename)
        self._config.filename = new_filename

        self._reset_image_pz()
        self.render()

        # FIXME: get new polydata ready

        self._state = STATE_IMAGE_LOADED

        
    def _set_image_viewer_dummy_input(self):
        ds = vtk.vtkImageGridSource()
        self._viewer.SetInput(ds.GetOutput())

    def _open_image_file(self, filename):
        # create a new instance of the current reader
        # to read the passed file.
        nr = self._reader.NewInstance()
        nr.SetFileName(filename)
        # FIXME: trap this error
        nr.Update()
        return nr




