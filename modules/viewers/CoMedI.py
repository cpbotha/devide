# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

# skeleton of an AUI-based viewer module
# copy and modify for your own purposes.

# set to False for 3D viewer, True for 2D image viewer
IMAGE_VIEWER = True

MATCH_MODE_PASSTHROUGH = 0
MATCH_MODE_LANDMARK_SS = 1

MATCH_MODE_STRINGS = [ \
        'Single structure landmarks'
        ]

COMPARISON_MODE_DATA2M = 0
COMPARISON_MODE_CHECKERBOARD = 1

# import the frame, i.e. the wx window containing everything
import CoMedIFrame
# and do a reload, so that the GUI is also updated at reloads of this
# module.
reload(CoMedIFrame)

import comedi_match_modes
reload(comedi_match_modes)

import comedi_comparison_modes
reload(comedi_comparison_modes)

import comedi_utils
reload(comedi_utils)

import math
from module_kits.misc_kit import misc_utils
from module_base import ModuleBase
from module_mixins import IntrospectModuleMixin
import module_utils
import operator
import os
import random #temp testing
import sys
import traceback
import vtk
import wx

class CoMedI(IntrospectModuleMixin, ModuleBase):
    # API methods
    def __init__(self, module_manager):
        """Standard constructor.  All DeVIDE modules have these, we do
        the required setup actions.
        """

        # we record the setting here, in case the user changes it
        # during the lifetime of this model, leading to different
        # states at init and shutdown.
        self.IMAGE_VIEWER = IMAGE_VIEWER

        ModuleBase.__init__(self, module_manager)

        IntrospectModuleMixin.__init__(
            self,
            {'Module (self)' : self})

        # create the view frame
        self._view_frame = module_utils.instantiate_module_view_frame(
            self, self._module_manager, 
            CoMedIFrame.CoMedIFrame)
        # change the title to something more spectacular
        self._view_frame.SetTitle('CoMedI')


        self._setup_vis()


        # hook up all event handlers
        self._bind_events()

        # make our window appear (this is a viewer after all)
        self.view()
        # all modules should toggle this once they have shown their
        # views. 
        self.view_initialised = True

        # this will cause the correct set_cam_* call to be made
        self._config.cam_parallel = False

        # setup all match modes here.  even if the user switches
        # modes, all metadata should be serialised, so that after a
        # network reload, the user can switch and will get her old
        # metadata back from a previous session.
        self._config.sstructlandmarksmm_cfg = {}

        # default match mode is the landmark thingy
        self._config.match_mode = MATCH_MODE_LANDMARK_SS
        # this will hold a binding to the current match mode that will
        # be initially setup by config_to_logic
        self.match_mode = None

        self._config.data2mcm_cfg = {}
        self._config.checkerboardcm_cfg = {}

        self._config.comparison_mode = COMPARISON_MODE_DATA2M
        self.comparison_mode = None

        # apply config information to underlying logic
        self.sync_module_logic_with_config()
        # then bring it all the way up again to the view
        self.sync_module_view_with_logic()


    def close(self):
        """Clean-up method called on all DeVIDE modules when they are
        deleted.
        """

        # get rid of match_mode
        self.match_mode.close()

        self._close_vis()
        
        # now take care of the wx window
        self._view_frame.close()
        # then shutdown our introspection mixin
        IntrospectModuleMixin.close(self)

    def get_input_descriptions(self):
        # define this as a tuple of input descriptions if you want to
        # take input data e.g. return ('vtkPolyData', 'my kind of
        # data')
        return ('Data 1', 'Data 2')

    def get_output_descriptions(self):
        # define this as a tuple of output descriptions if you want to
        # generate output data.
        return ('Matched Data 2', 'Confidence Field')



    def set_input(self, idx, input_stream):
        # this gets called right before you get executed.  take the
        # input_stream and store it so that it's available during
        # execute_module()

        if idx == 0:
            self._data1_slice_viewer.set_input(input_stream)

            if input_stream is None:
                # we're done disconnecting, no syncing necessary
                # but we do need to tell the current match_mode
                # something is going on.
                self._update_mmcm()
                return

            if not self._data2_slice_viewer.get_input():
                self._data1_slice_viewer.reset_camera()
                self._data1_slice_viewer.render()

            else:
                # sync ourselves to data2
                self.sync_slice_viewers.sync_all(
                        self._data2_slice_viewer,
                        [self._data1_slice_viewer])


        if idx == 1:
            self._data2_slice_viewer.set_input(input_stream)

            if input_stream is None:
                self._update_mmcm()
                return

            if not self._data1_slice_viewer.get_input():
                self._data2_slice_viewer.reset_camera()
                self._data2_slice_viewer.render()

            else:
                self.sync_slice_viewers.sync_all(
                        self._data1_slice_viewer,
                        [self._data2_slice_viewer])



    def get_output(self, idx):
        # this can get called at any time when a consumer module wants
        # you output data.
        if idx == 0:
            return self.match_mode.get_output()
        else:
            return self.match_mode.get_confidence()

    def execute_module(self):
        # when it's you turn to execute as part of a network
        # execution, this gets called.
        pass

    # as per usual with viewer modules, we're keeping the config up to
    # date throughout execution, so only the config_to_logic and
    # config_to_view are implemented, so that things correctly restore
    # after a deserialisation.

    def logic_to_config(self):
        pass

    def config_to_logic(self):
        # we need to be able to build up the correct MatchMode based
        # on the config.
        self._sync_mm_with_config()
        # do the same for the comparison mode
        self._sync_cm_with_config()


    def config_to_view(self):
        if self._config.cam_parallel:
            self.set_cam_parallel()
            # also make sure this is reflected in the menu
            self._view_frame.set_cam_parallel()
        else:
            self.set_cam_perspective()
            # also make sure this is reflected in the menu
            self._view_frame.set_cam_perspective()

        # now also set the correct pages in the match mode and
        # comparison mode notebooks.
        vf = self._view_frame
        cp = vf.pane_controls.window

        # ChangeSelection does not trigger the event handlers
        cp.match_mode_notebook.ChangeSelection(
                self._config.match_mode)

        cp.comparison_mode_notebook.ChangeSelection(
                self._config.comparison_mode)



    def view_to_config(self):
        pass

    def view(self):
        self._view_frame.Show()
        self._view_frame.Raise()

        # because we have an RWI involved, we have to do this
        # SafeYield, so that the window does actually appear before we
        # call the render.  If we don't do this, we get an initial
        # empty renderwindow.
        wx.SafeYield()
        self.render_all()

    # PRIVATE methods
    def _bind_events(self):
        """Bind wx events to Python callable object event handlers.
        """
        vf = self._view_frame

        vf.Bind(wx.EVT_MENU, self._handler_cam_perspective,
                id = vf.id_camera_perspective)
        vf.Bind(wx.EVT_MENU, self._handler_cam_parallel,
                id = vf.id_camera_parallel)

        vf.Bind(wx.EVT_MENU, self._handler_cam_xyzp,
                id = vf.id_camera_xyzp)


        vf.Bind(wx.EVT_MENU, self._handler_introspect,
                id = vf.id_adv_introspect)

        vf.Bind(wx.EVT_MENU, self._handler_synced,
                id = vf.id_views_synchronised)

        vf.Bind(wx.EVT_MENU, self._handler_slice2,
                id = vf.id_views_slice2)

        vf.Bind(wx.EVT_MENU, self._handler_slice3,
                id = vf.id_views_slice3)

        cp = vf.pane_controls.window
        cp.compare_button.Bind(wx.EVT_BUTTON, self._handler_compare)
        cp.update_compvis_button.Bind(wx.EVT_BUTTON,
                self._handler_update_compvis)

        cp.match_mode_notebook.Bind(
                wx.EVT_NOTEBOOK_PAGE_CHANGED,
                self._handler_mm_nbp_changed)

        cp.comparison_mode_notebook.Bind(
                wx.EVT_NOTEBOOK_PAGE_CHANGED,
                self._handler_cm_nbp_changed)

    def _close_vis(self):
        for sv in self._slice_viewers:
            sv.close()

    def _handler_cam_parallel(self, event):
        self.set_cam_parallel()

    def _handler_cam_perspective(self, event):
        self.set_cam_perspective()

    def _handler_cam_xyzp(self, event):
        self._data1_slice_viewer.reset_to_default_view(2)
        # then synchronise the rest
        self.sync_slice_viewers.sync_all(self._data1_slice_viewer)

    def _handler_cm_nbp_changed(self, evt):
        # tab indices match the constant value.
        self._config.comparison_mode = evt.GetSelection()
        self._sync_cm_with_config()
        self.comparison_mode.update_vis()

        # we have to call this skip so that wx also changes the page
        # contents.
        evt.Skip()

    def _handler_mm_nbp_changed(self, evt):
        print "hello you too"
        # we have to call this skip so wx also changes the actual tab
        # contents.
        evt.Skip()

    def _handler_compare(self, e):
        self._update_mmcm()

    def _handler_introspect(self, e):
        self.miscObjectConfigure(self._view_frame, self, 'CoMedI')

    def _handler_slice2(self, e):
        for sv in self.sync_slice_viewers.slice_viewers:
            if e.IsChecked():
                sv.activate_slice(1)
            else:
                sv.deactivate_slice(1)

    def _handler_slice3(self, e):
        for sv in self.sync_slice_viewers.slice_viewers:
            if e.IsChecked():
                sv.activate_slice(2)
            else:
                sv.deactivate_slice(2)

    def _handler_synced(self, event):
        #cb = event.GetEventObject()
        if event.IsChecked():
            if not self.sync_slice_viewers.sync:
                self.sync_slice_viewers.sync = True
                # now do the initial sync to data1
                self.sync_slice_viewers.sync_all(
                        self._data1_slice_viewer)

        else:
            self.sync_slice_viewers.sync = False

    def _handler_update_compvis(self, evt):
        self.comparison_mode.update_vis()

    def _observer_cursor(self, vtk_o, vtk_e, txt):
        """
        @param txt: Text identifier that will be prepended to the
        cursor position update in the UI.
        """
        cd =  [0,0,0,0]
        cdv = vtk_o.GetCursorData(cd)
        if not cdv:
            # we're not cursoring
            return

        c = tuple([int(i) for i in cd])
        self._view_frame.pane_controls.window.cursor_text.SetValue(
                '%s : %s = %d' % (txt, c[0:3], c[3]))

        # also store the current cursor position in an ivar, we need
        # it.  we probably need to replace this text check with
        # something else...
        if txt.startswith('d1'):
            self._data1_slice_viewer.current_index_pos = c
            w = self._data1_slice_viewer.get_world_pos(c)
            self._data1_slice_viewer.current_world_pos = w
        elif txt.startswith('d2'):
            self._data1_slice_viewer.current_index_pos = c
            w = self._data2_slice_viewer.get_world_pos(c)
            self._data2_slice_viewer.current_world_pos = w

    def _setup_vis(self):
        # setup data1 slice viewer, instrument its slice viewers with
        # observers so that the cursor information is output to the
        # GUI
        SV = comedi_utils.CMSliceViewer
        self._data1_slice_viewer = SV(
                self._view_frame.rwi_pane_data1.rwi,
                self._view_frame.rwi_pane_data1.renderer)
        for ipw in self._data1_slice_viewer.ipws:
            ipw.AddObserver(
                'InteractionEvent', 
                lambda o,e: self._observer_cursor(o,e,'d1') )

        # do the same for the data2 slice viewer
        self._data2_slice_viewer = SV(
                self._view_frame.rwi_pane_data2.rwi,
                self._view_frame.rwi_pane_data2.renderer)
        for ipw in self._data2_slice_viewer.ipws:
            ipw.AddObserver(
                'InteractionEvent', 
                lambda o,e: self._observer_cursor(o,e,'d2') )

        self._slice_viewers = [ \
                self._data1_slice_viewer,
                self._data2_slice_viewer]

        self.sync_slice_viewers = ssv = comedi_utils.SyncSliceViewers()
        for sv in self._slice_viewers:
            ssv.add_slice_viewer(sv)

    def _sync_cm_with_config(self):
        """Synchronise comparison mode with what's specified in the
        config.  This is used by config_to_logic as well as the
        run-time comparison mode tab switching.
        """
        if self.comparison_mode:
            self.comparison_mode.close()
            self.comparison_mode = None


        if self._config.comparison_mode == COMPARISON_MODE_DATA2M:
            cm = comedi_comparison_modes.Data2MCM
            self.comparison_mode = cm(
                    self, self._config.data2mcm_cfg)

        elif self._config.comparison_mode == \
                COMPARISON_MODE_CHECKERBOARD:
                    cm = comedi_comparison_modes.CheckerboardCM
                    self.comparison_mode = cm(
                            self, self._config.checkerboardcm_cfg)


    def _sync_mm_with_config(self):
        """Synchronise match mode with what's specified in the config.
        This is used by config_to_logic as well as the run-time match
        mode tab switching.
        """

        if self.match_mode:
            self.match_mode.close()
            self.match_mode = None

        if self._config.match_mode == MATCH_MODE_LANDMARK_SS:
            # we have to create a new one in anycase!  This gets
            # called if we get a brand new config given to us, too
            # much could have changed.
            #if mm.__class__.__name__ != SStructLandmarksMM.__name__:
            self.match_mode = comedi_match_modes.SStructLandmarksMM(
                        self, self._config.sstructlandmarksmm_cfg)


    def _update_mmcm(self):
        """Update the current match mode and the comparison mode.
        """

        self.match_mode.transform()
        self.comparison_mode.update_vis()

       
    # PUBLIC methods

    def get_compvis_vtk(self):
        """Return rwi and renderer used for the compvis.  Used mostly
        by the various comparison modes.
        """
        return (
                self._view_frame.rwi_pane_compvis.rwi,
                self._view_frame.rwi_pane_compvis.renderer
                )
    def get_data1(self):
        """Return data1 input.
        """
        return self._data1_slice_viewer.get_input()

    def get_data2m(self):
        """Return currently matched data2, i.e. the output of the
        current match mode.
        """
        return self.match_mode.get_output()

    def render_all(self):
        """Method that calls Render() on the embedded RenderWindow.
        Use this after having made changes to the scene.
        """
        self._view_frame.render_all()

    def set_cam_perspective(self):
        for sv in self.sync_slice_viewers.slice_viewers:
            sv.set_perspective()
            sv.render()

        self._config.cam_parallel = False

    def set_cam_parallel(self):
        for sv in self.sync_slice_viewers.slice_viewers:
            sv.set_parallel()
            sv.render()

        self._config.cam_parallel = True    



