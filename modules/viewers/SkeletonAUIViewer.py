# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

# skeleton of an AUI-based viewer module
# copy and modify for your own purposes.

# import the frame, i.e. the wx window containing everything
import SkeletonAUIViewerFrame
# and do a reload, so that the GUI is also updated at reloads of this
# module.
reload(SkeletonAUIViewerFrame)

from module_kits.misc_kit import misc_utils
from module_base import ModuleBase
from module_mixins import IntrospectModuleMixin
import module_utils
import os
import sys
import traceback
import vtk
import wx

class SkeletonAUIViewer(IntrospectModuleMixin, ModuleBase):
    def __init__(self, module_manager):
        """Standard constructor.  All DeVIDE modules have these, we do
        the required setup actions.
        """

        ModuleBase.__init__(self, module_manager)

        IntrospectModuleMixin.__init__(
            self,
            {'Module (self)' : self})

        # create the view frame
        self._view_frame = module_utils.instantiate_module_view_frame(
            self, self._module_manager, 
            SkeletonAUIViewerFrame.SkeletonAUIViewerFrame)
        # change the title to something more spectacular
        self._view_frame.SetTitle('Skeleton AUI Viewer')

        # create the necessary VTK objects: we only need a renderer,
        # the RenderWindowInteractor in the view_frame has the rest.
        self.ren = vtk.vtkRenderer()
        self.ren.SetBackground(0.5,0.5,0.5)
        self._view_frame.rwi.GetRenderWindow().AddRenderer(self.ren)

        # hook up all event handlers
        self._bind_events()

        # anything you stuff into self._config will be saved
        self._config.my_string = 'la la'

        # make our window appear (this is a viewer after all)
        self.view()
        # all modules should toggle this once they have shown their
        # views. 
        self.view_initialised = True

        # apply config information to underlying logic
        self.sync_module_logic_with_config()
        # then bring it all the way up again to the view
        self.sync_module_view_with_logic()

    def close(self):
        """Clean-up method called on all DeVIDE modules when they are
        deleted.
        """
        
        # with this complicated de-init, we make sure that VTK is 
        # properly taken care of
        self.ren.RemoveAllViewProps()
        # this finalize makes sure we don't get any strange X
        # errors when we kill the module.
        self._view_frame.rwi.GetRenderWindow().Finalize()
        self._view_frame.rwi.SetRenderWindow(None)
        del self._view_frame.rwi
        # done with VTK de-init

        # now take care of the wx window
        self._view_frame.close()
        # then shutdown our introspection mixin
        IntrospectModuleMixin.close(self)

    def get_input_descriptions(self):
        # define this as a tuple of input descriptions if you want to
        # take input data e.g. return ('vtkPolyData', 'my kind of
        # data')
        return ()

    def get_output_descriptions(self):
        # define this as a tuple of output descriptions if you want to
        # generate output data.
        return ()

    def set_input(self, idx, input_stream):
        # this gets called right before you get executed.  take the
        # input_stream and store it so that it's available during
        # execute_module()
        pass

    def get_output(self, idx):
        # this can get called at any time when a consumer module wants
        # you output data.
        pass

    def execute_module(self):
        # when it's you turn to execute as part of a network
        # execution, this gets called.
        pass

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

        # because we have an RWI involved, we have to do this
        # SafeYield, so that the window does actually appear before we
        # call the render.  If we don't do this, we get an initial
        # empty renderwindow.
        wx.SafeYield()
        self.render()

    def add_superquadric(self):
        """Add a new superquadric at a random position.

        This is called by the event handler for the 'Add Superquadric'
        button.
        """

        import random

        # let's add a superquadric actor to the renderer
        sqs = vtk.vtkSuperquadricSource()
        sqs.ToroidalOn()
        sqs.SetSize(0.1) # default is 0.5
        m = vtk.vtkPolyDataMapper()
        m.SetInput(sqs.GetOutput())
        a = vtk.vtkActor()
        a.SetMapper(m)
        pos = [random.random() for _ in range(3)]
        a.SetPosition(pos)
        a.GetProperty().SetColor([random.random() for _ in range(3)])
        self.ren.AddActor(a)
        self.render()

        # add string to files listcontrol showing where the
        # superquadric was placed.
        self._view_frame.files_lc.InsertStringItem(
                sys.maxint, 'Position (%.2f, %.2f, %.2f)' % tuple(pos))


    def _bind_events(self):
        """Bind wx events to Python callable object event handlers.
        """

        vf = self._view_frame
        vf.Bind(wx.EVT_MENU, self._handler_file_open,
                id = vf.id_file_open)

        self._view_frame.button1.Bind(wx.EVT_BUTTON,
                self._handler_button1)
        self._view_frame.button2.Bind(wx.EVT_BUTTON,
                self._handler_button2)

    def _handler_button1(self, event):
        print "button1 pressed"

        self.add_superquadric()

    def _handler_button2(self, event):
        print "button2 pressed"

        self.ren.ResetCamera()
        self.render()

    def _handler_file_open(self, event):
        print "could have opened file now"

    def render(self):
        """Method that calls Render() on the embedded RenderWindow.
        Use this after having made changes to the scene.
        """
        self._view_frame.render()



        

