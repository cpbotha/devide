# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

import SkeletonAUIViewerFrame
reload(SkeletonAUIViewerFrame)

from module_kits.misc_kit import misc_utils
from moduleBase import moduleBase
from moduleMixins import introspectModuleMixin
import moduleUtils
import os
import sys
import traceback
import vtk
import wx

class SkeletonAUIViewer(introspectModuleMixin, moduleBase):
    def __init__(self, module_manager):
        moduleBase.__init__(self, module_manager)

        introspectModuleMixin.__init__(
            self,
            {'Module (self)' : self})

        self._view_frame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager, 
            SkeletonAUIViewerFrame.SkeletonAUIViewerFrame)
        # change the title to something more spectacular
        # default is SkeletonAUIViewer View
        self._view_frame.SetTitle('Skeleton AUI Viewer')

        self.ren = vtk.vtkRenderer()
        self._view_frame.rwi.GetRenderWindow().AddRenderer(self.ren)

        self._bind_events()


        # this will be saved along with any network
        self._config.my_string = 'la la'

        self.sync_module_logic_with_config()
        self.sync_module_view_with_logic()

        self.view()
        # all modules should toggle this once they have shown their
        # stuff.
        self.view_initialised = True

        if os.name == 'posix':
            # bug with GTK where the image window appears bunched up
            # in the top-left corner.  By setting the default view
            # (again), it's worked around
            #self._view_frame.set_default_view()
            pass

    def close(self):
        
        # with this complicated de-init, we make sure that VTK is 
        # properly taken care of
        self._view_frame.rwi

        self.ren.RemoveAllViewProps()
        # this finalize makes sure we don't get any strange X
        # errors when we kill the module.
        self._view_frame.rwi.GetRenderWindow().Finalize()
        self._view_frame.rwi.SetRenderWindow(None)
        del self._view_frame.rwi
        # done with VTK de-init

        self._view_frame.close()
        introspectModuleMixin.close(self)

    def get_input_descriptions(self):
        return ()

    def get_output_descriptions(self):
        return ()

    def set_input(self, idx, input_stream):
        pass

    def get_output(self, idx):
        pass

    def execute_module(self):
        pass

    def logic_to_config(self):
        pass

    def config_to_logic(self):
        pass

    def config_to_view(self):
        pass

    def view_to_config(self):
        # self._config is maintained in real-time
        pass

    def view(self):
        self._view_frame.Show()
        self._view_frame.Raise()

        # because we have an RWI involved, we have to do this
        # SafeYield, so that the window does actually appear before we
        # call the render.  If we don't do this, we get an initial
        # empty renderwindow.
        wx.SafeYield()
        self._view_frame.render_image()

    def _bind_events(self):
        vf = self._view_frame
        vf.Bind(wx.EVT_MENU, self._handler_file_open,
                id = vf.id_file_open)

        self._view_frame.button1.Bind(wx.EVT_BUTTON,
                self._handler_button1)
        self._view_frame.button2.Bind(wx.EVT_BUTTON,
                self._handler_button2)

    def _handler_button1(self, event):
        print "button1 pressed"

    def _handler_button2(self, event):
        print "button2 pressed"

    def _handler_file_open(self, event):
        print "would have opened file now"

    def _set_image_viewer_dummy_input(self):
        ds = vtk.vtkImageGridSource()
        self._image_viewer.SetInput(ds.GetOutput())



        

