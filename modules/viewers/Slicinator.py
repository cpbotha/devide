# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

# NOTES:
# you can't put the RWI in a StaticBox, it never manages to appear.

# http://www.nabble.com/vtkContourWidget-with-vtkImageViewer2-td18485627.html
# has more information on how to use the vtkContourWidget

# MITK does segmentation on all three orthogonal directions.  For more
# info: http://www.mitk.org/slicebasedsegmentation.html

# to scan convert polygon, you could use: vtkPolyDataToImageStencil
# see the example linked to in the VTK documentation (should be the
# same as the ImageTracerWidget example)
# I checked the documentation, it SHOULD work for 2D as well.

# NBNBNB
# think about having bitmaps as the primary storage (or stencils)
# you also start with a regiongrowing (for example)
# can always convert to polygon to do stuff there, convert back
# add mode, subtract mode, current object, delete (like MITK)
# also list of objects with checkboxes for vis and buttons to change
# colour
# snake still missing


# general requirements:
# * multiple objects (i.e. multiple coloured contours per slice)

# slice segmentation modes:
# * polygon mode
# * freehand drawing
# * 2d levelset

# see design notes on p39 of AM2 moleskine

# mask volume import! (user clicks import, gets to select from which
# input) - mask volume is contoured.

# add reset image button just like the DICOMBrowser
# mouse wheel should go to next/previous slice

from module_base import ModuleBase
from module_mixins import IntrospectModuleMixin
import module_utils
import vtk
import wx

class Contour:
    pass

class Object:
    pass

class Slicinator(IntrospectModuleMixin, ModuleBase):
    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        # internal variables

        # config variables
        self._config.somevar = 3

        self._view_frame = None
        self._create_view_frame()
        self._create_vtk_pipeline()

        # dummy input has been set by create_vtk_pipeline, we this
        # ivar we record that we are not connected.
        self._input_data = None


        self._bind_events()

        self.view()
        # all modules should toggle this once they have shown their
        # stuff.
        self.view_initialised = True

        self.config_to_logic()
        self.logic_to_config()
        self.config_to_view()
        


    def close(self):
        # with this complicated de-init, we make sure that VTK is 
        # properly taken care of
        self._image_viewer.GetRenderer().RemoveAllViewProps()
        self._image_viewer.SetupInteractor(None)
        self._image_viewer.SetRenderer(None)
        # this finalize makes sure we don't get any strange X
        # errors when we kill the module.
        self._image_viewer.GetRenderWindow().Finalize()
        self._image_viewer.SetRenderWindow(None)
        self._image_viewer.DebugOn()
        del self._image_viewer
        # done with VTK de-init
     
        self._view_frame.Destroy()
        del self._view_frame

        IntrospectModuleMixin.close(self)
        ModuleBase.close(self)

    def execute_module(self):
        pass

    def get_input_descriptions(self):
        return ('Input VTK image data',)

    def set_input(self, idx, input_data):
        if input_data == self._input_data:
            return

        # handle disconnects
        if input_data is None:
            self._input_data = None
            self._set_image_viewer_dummy_input()

        else:
            # try and link this up
            # method will throw an exception if not valid
            self._set_image_viewer_input(input_data)
            # if we get here, connection was successful
            self._input_data = input_data

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

        # because we have an RWI involved, we have to do this
        # SafeYield, so that the window does actually appear before we
        # call the render.  If we don't do this, we get an initial
        # empty renderwindow.
        wx.SafeYield()
        self._render()

    # end of API calls

    def _bind_events(self):
        self._view_frame.reset_image_button.Bind(
                wx.EVT_BUTTON, self._handler_reset_image_button)

    def _create_view_frame(self):
        import resources.python.slicinator_frames
        reload(resources.python.slicinator_frames)

        self._view_frame = module_utils.instantiate_module_view_frame(
            self, self._module_manager,
            resources.python.slicinator_frames.SlicinatorFrame)

        vf = self._view_frame

    def _create_vtk_pipeline(self):
        if False:
            vf = self._view_frame
            ren = vtk.vtkRenderer()
            vf.rwi.GetRenderWindow().AddRenderer(ren)

        else:
            self._image_viewer = vtk.vtkImageViewer2()
            self._image_viewer.SetupInteractor(self._view_frame.rwi)
            self._image_viewer.GetRenderer().SetBackground(0.3,0.3,0.3)

            self._set_image_viewer_dummy_input()

    def _handler_reset_image_button(self, event):
        self._reset_image()

    def _init_cw(self):
        self._cw = vtk.vtkContourWidget()

        rep = vtk.vtkOrientedGlyphContourRepresentation()
        self._cw.SetRepresentation(rep)

        iapp = vtk.vtkImageActorPointPlacer()
        iapp.SetImageActor(self._image_viewer.GetImageActor())
        rep.SetPointPlacer(iapp)

        self._cw.SetInteractor(self._view_frame.rwi)
        self._cw.On()

    def _render(self):
        self._image_viewer.Render()
        #self._view_frame.rwi.Render()

    def _reset_image(self):
        self._reset_image_wl()
        self._reset_image_pz()
        self._render()

    def _reset_image_pz(self):
        """Reset the pan/zoom of the current image.
        """

        ren = self._image_viewer.GetRenderer()
        ren.ResetCamera()

    def _reset_image_wl(self):
        """Reset the window/level of the current image.

        This assumes that the image has already been read and that it
        has a valid scalar range.
        """
        iv = self._image_viewer
        inp = iv.GetInput()
        if inp:
            r = inp.GetScalarRange()
            iv.SetColorWindow(r[1] - r[0])
            iv.SetColorLevel(0.5 * (r[1] + r[0]))
       

    def _set_image_viewer_dummy_input(self):
        ds = vtk.vtkImageGridSource()
        self._image_viewer.SetInput(ds.GetOutput())

    def _set_image_viewer_input(self, input_data):
        try:
            if not input_data.IsA('vtkImageData'):
                raise RuntimeError('Invalid input data.')
        except AttributeError:
            raise RuntimeError('Invalid input data.')

        self._image_viewer.SetInput(input_data)
        # module.set_input() only gets called right before an
        # execute_module, so we can do our thing here.
        self._reset_image()
        
        we = input_data.GetWholeExtent()
        min,max = we[4], we[5]
        self._reset_slice_spin(min, min, max)

    def _reset_slice_spin(self, val, min, max):
        self._view_frame.slice_spin.SetValue(val)
        self._view_frame.slice_spin.SetRange(min,max)

        


    


