# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

# skeleton of an AUI-based viewer module
# copy and modify for your own purposes.

# set to False for 3D viewer, True for 2D image viewer
IMAGE_VIEWER = True

# import the frame, i.e. the wx window containing everything
import CoMedIFrame
# and do a reload, so that the GUI is also updated at reloads of this
# module.
reload(CoMedIFrame)

from module_kits.misc_kit import misc_utils
from module_base import ModuleBase
from module_mixins import IntrospectModuleMixin
import module_utils
import os
import sys
import traceback
import vtk
import wx

class DVOrientationWidget:
    """Convenience class for embedding orientation widget in any
    renderwindowinteractor.  If the data has DeVIDE style orientation
    metadata, this class will show the little LRHFAP block, otherwise
    x-y-z cursor.
    """

    def __init__(self, rwi):


        self._orientation_widget = vtk.vtkOrientationMarkerWidget()
        self._orientation_widget.SetInteractor(rwi)

        # we'll use this if there is no orientation metadata
        # just a thingy with x-y-z indicators
        self._axes_actor = vtk.vtkAxesActor()

        # we'll use this if there is orientation metadata
        self._annotated_cube_actor = aca = vtk.vtkAnnotatedCubeActor()

        # configure the thing with better colours and no stupid edges 
        #aca.TextEdgesOff()
        aca.GetXMinusFaceProperty().SetColor(1,0,0)
        aca.GetXPlusFaceProperty().SetColor(1,0,0)
        aca.GetYMinusFaceProperty().SetColor(0,1,0)
        aca.GetYPlusFaceProperty().SetColor(0,1,0)
        aca.GetZMinusFaceProperty().SetColor(0,0,1)
        aca.GetZPlusFaceProperty().SetColor(0,0,1)
       

    def close(self):
        self.set_input(None)
        self._orientation_widget.SetInteractor(None)


    def set_input(self, input_data):
        if input_data is None:
            self._orientation_widget.Off()
            return

        ala = input_data.GetFieldData().GetArray('axis_labels_array')
        if ala:
            lut = list('LRPAFH')
            labels = []
            for i in range(6):
                labels.append(lut[ala.GetValue(i)])
                
            self._set_annotated_cube_actor_labels(labels)
            self._orientation_widget.Off()
            self._orientation_widget.SetOrientationMarker(
                self._annotated_cube_actor)
            self._orientation_widget.On()
            
        else:
            self._orientation_widget.Off()
            self._orientation_widget.SetOrientationMarker(
                self._axes_actor)
            self._orientation_widget.On()

    def _set_annotated_cube_actor_labels(self, labels):
        aca = self._annotated_cube_actor
        aca.SetXMinusFaceText(labels[0])
        aca.SetXPlusFaceText(labels[1])
        aca.SetYMinusFaceText(labels[2])
        aca.SetYPlusFaceText(labels[3])
        aca.SetZMinusFaceText(labels[4])
        aca.SetZPlusFaceText(labels[5])



class CMSliceViewer:
    """Simple class for enabling 1 or 3 ortho slices in a 3D scene.
    """

    def __init__(self, rwi, renderer):
        self._rwi = rwi
        self._renderer = renderer

        istyle = vtk.vtkInteractorStyleTrackballCamera()
        rwi.SetInteractorStyle(istyle)

        self.ipw1 = vtk.vtkImagePlaneWidget()
        self.ipw1.SetInteractor(rwi)

        self.outline_source = vtk.vtkOutlineCornerFilter()
        m = vtk.vtkPolyDataMapper()
        m.SetInput(self.outline_source.GetOutput())
        a = vtk.vtkActor()
        a.SetMapper(m)
        self.outline_actor = a

        self.dv_orientation_widget = DVOrientationWidget(rwi)

    def close(self):
        self.set_input(None)
        self.dv_orientation_widget.close()

    def get_input(self):
        return self.ipw1.GetInput()

    def render(self):
        self._rwi.GetRenderWindow().Render()

    def reset_camera(self):
        self._renderer.ResetCamera()
        

    def set_input(self, input):
        if input == self.ipw1.GetInput():
            return

        if input is None:
            self.dv_orientation_widget.set_input(None)
            self.ipw1.SetInput(None)
            self.ipw1.Off()
            self._renderer.RemoveViewProp(self.outline_actor)
            self.outline_source.SetInput(None)

        else:
            self.ipw1.SetInput(input)
            self.ipw1.SetPlaneOrientation(2) # axial
            self.ipw1.SetSliceIndex(0)
            self.ipw1.On()
            self.outline_source.SetInput(input)
            self._renderer.AddViewProp(self.outline_actor)
            self.dv_orientation_widget.set_input(input)



class CoMedI(IntrospectModuleMixin, ModuleBase):
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
        return ()

    def _handler_introspect(self, e):
        self.miscObjectConfigure(self._view_frame, self, 'CoMedI')

    def set_input(self, idx, input_stream):
        # this gets called right before you get executed.  take the
        # input_stream and store it so that it's available during
        # execute_module()

        if idx == 0:
            self._data1_slice_viewer.set_input(input_stream)
            if not self._data2_slice_viewer.get_input():
                self._data1_slice_viewer.reset_camera()
            self._data1_slice_viewer.render()

        if idx == 1:
            self._data2_slice_viewer.set_input(input_stream)
            if not self._data1_slice_viewer.get_input():
                self._data2_slice_viewer.reset_camera()
            self._data2_slice_viewer.render()

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
        self.render_all()

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
        vf.Bind(wx.EVT_MENU, self._handler_introspect,
                id = vf.id_adv_introspect)

    def _handler_button1(self, event):
        print "button1 pressed"

        self.add_superquadric()

    def _handler_button2(self, event):
        print "button2 pressed"

        self.ren.ResetCamera()
        self.render()

    def _handler_file_open(self, event):
        print "could have opened file now"

    def render_all(self):
        """Method that calls Render() on the embedded RenderWindow.
        Use this after having made changes to the scene.
        """
        self._view_frame.render_all()

    def _setup_vis(self):
        self._data1_slice_viewer = CMSliceViewer(
                self._view_frame.rwi_pane_data1.rwi,
                self._view_frame.rwi_pane_data1.renderer)

        self._data2_slice_viewer = CMSliceViewer(
                self._view_frame.rwi_pane_data2.rwi,
                self._view_frame.rwi_pane_data2.renderer)

        self._data2m_slice_viewer = CMSliceViewer(
                self._view_frame.rwi_pane_data2m.rwi,
                self._view_frame.rwi_pane_data2m.renderer)
              

    def _close_vis(self):
        self._data1_slice_viewer.close()
        self._data2_slice_viewer.close()
        self._data2m_slice_viewer.close()

