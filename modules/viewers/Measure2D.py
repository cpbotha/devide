import geometry
from moduleBase import moduleBase
from moduleMixins import introspectModuleMixin
import moduleUtils
import Measure2DFrame
reload(Measure2DFrame)

import vtk
import vtktud
import wx

class Measure2D(introspectModuleMixin, moduleBase):
    def __init__(self, module_manager):
        moduleBase.__init__(self, module_manager)

        self._view_frame = None
        self._viewer = None
        self._input_image = None
        self._dummy_image_source = vtk.vtkImageMandelbrotSource()
        
        self._widgets = []

        # build frame
        self._view_frame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager, Measure2DFrame.Measure2DFrame)

        # now link up all event handlers
        self._bind_events()

        # then build VTK pipeline
        self._create_vtk_pipeline()

        # set us up with dummy input
        self._setup_new_image()

        # show everything
        self.view()

        
    def close(self):
        if self._view_frame is not None:
            self._view_frame.close()
            
    def view(self):
        self._view_frame.Show()
        self._view_frame.Raise()

        # GOTCHA!! (finally)
        # we need to do this to make sure that the Show() and Raise() above
        # are actually performed.  Not doing this is what resulted in the
        # "empty renderwindow" bug after module reloading, and also in the
        # fact that shortly after module creation dummy data rendered outside
        # the module frame.
        # YEAH.
        wx.SafeYield()

        self.render()

        # so if we bring up the view after having executed the network once,
        # re-executing will not do a set_input()!  (the scheduler doesn't
        # know that the module is now dirty)  Two solutions:
        # * make module dirty when view is activated
        # * activate view at instantiation. <--- we're doing this now.
        
    def get_input_descriptions(self):
        return ('Image data',)

    def get_output_descriptions(self):
        return ()

    def execute_module(self):
        pass

    def logic_to_config(self):
        pass

    def config_to_logic(self):
        pass
    
    def set_input(self, idx, input_stream):
        if self._input_image != input_stream:
            self._input_image = input_stream
            self._setup_new_image()
            
    def _bind_events(self):
        """Setup all event handling based on the view frame.
        """
                
        slice_slider = self._view_frame._image_control_panel.slider
        slice_slider.Bind(wx.EVT_SLIDER, self._handler_slice_slider)
        
        new_measurement_button = self._view_frame._measurement_panel.new_button
        new_measurement_button.Bind(wx.EVT_BUTTON, self._handler_new_measurement_button)

    def _create_vtk_pipeline(self):
        """Create pipeline for viewing 2D image data.
        
        """
        if self._viewer is None and not self._view_frame is None:
            #self._ren = vtk.vtkRenderer()
            #self._ren.SetBackground(0.5,0.5,0.5)
            #self._view_frame._rwi.GetRenderWindow().AddRenderer(self._ren)
            
            #self._image_actor = vtk.vtkImageActor()
            #self._ren.AddViewProp(self._image_actor)
            
            # could be that input has already been set, but that view was
            # instantiated later.
            
            if True:
                self._viewer = vtk.vtkImageViewer2()
                self._viewer.SetupInteractor(self._view_frame._rwi)
                self._viewer.GetRenderer().SetBackground(0.3,0.3,0.3)
                
            else:
                ren = vtk.vtkRenderer()
                self._view_frame._rwi.GetRenderWindow().AddRenderer(ren)
            

    def _handler_new_measurement_button(self, event):
        
        widget_type = 0


        if widget_type == 0:
            w = vtktud.vtkEllipseWidget()
            w.SetInteractor(self._view_frame._rwi)
            #w.PlaceWidget(0, 50, 0, 50, 0, 0)
            w.SetEnabled(1)
            self._widgets.append(w)
        
        elif widget_type == 1:
            handle = vtk.vtkPointHandleRepresentation2D()
            handle.GetProperty().SetColor(1,0,0)

            rep = vtk.vtkDistanceRepresentation2D()
            rep.SetHandleRepresentation(handle)
            rep.GetAxis().SetNumberOfMinorTicks(4)
            rep.GetAxis().SetTickLength(9)
            rep.GetAxis().SetTitlePosition(0.2)
        
            w = vtk.vtkDistanceWidget()
            w.SetInteractor(self._view_frame._rwi)        
            #w.CreateDefaultRepresentation()
            w.SetRepresentation(rep)
        
            w.SetEnabled(1)

            self._widgets.append(w)
            
        else:
            def observer_test(widget):
                rep = widget.GetRepresentation()
                
                # get four world points
                p1w = [0.0,0.0,0.0]
                rep.GetPoint1WorldPosition(p1w)
                p2w = [0.0,0.0,0.0]
                rep.GetPoint2WorldPosition(p2w)
                p3w = [0.0,0.0,0.0]
                rep.GetPoint3WorldPosition(p3w)
                p4w = [0.0,0.0,0.0]
                rep.GetPoint4WorldPosition(p4w)

                # determine halfway between pair1, move pair2 along pair1
                # determine halfway between pair2, move pair1 along pair2
                # motion by definition orthogonal, so it converges
                l1n, l1m, l1 = geometry.normalise_line(p1w, p2w)
                l2n, l2m, l2 = geometry.normalise_line(p3w, p4w)

                tc1 = p1w + l1m / 2.0 * l1n # target center 1
                tc2 = p3w + l2m / 2.0 * l2n # target center 2

                p3w, p4w = geometry.move_line_to_target_along_normal(p3w, p4w, l1n, tc1)
                p1w, p2w = geometry.move_line_to_target_along_normal(p1w, p2w, l2n, tc2)

                l1n, l1m, l1 = geometry.normalise_line(p1w, p2w)
                l2n, l2m, l2 = geometry.normalise_line(p3w, p4w)

                # the new system has to be orthogonal (more or less), else
                # we don't apply it.
                if geometry.abs(geometry.dot(l1n, l2n)) < geometry.epsilon:
                    rep.SetPoint1WorldPosition(p1w)
                    rep.SetPoint2WorldPosition(p2w)
                    rep.SetPoint3WorldPosition(p3w)
                    rep.SetPoint4WorldPosition(p4w)

            
            rep = vtk.vtkBiDimensionalRepresentation2D()
            widget = vtk.vtkBiDimensionalWidget()
            widget.SetInteractor(self._view_frame._rwi)
            widget.SetRepresentation(rep)
            widget.AddObserver("EndInteractionEvent", lambda o, e: observer_test(widget))
            
            #widget.CreateDefaultRepresentation()
            
            widget.SetEnabled(1)
            self._widgets.append(widget)

        self.render()
            
    def _handler_slice_slider(self, event):
        if not self._input_image is None:
            val = self._view_frame._image_control_panel.slider.GetValue()
            self._viewer.SetSlice(val)

    def render(self):
        self._view_frame._rwi.Render()
                
    def _setup_new_image(self):
        """Based on the current self._input_image and the viewer, this thing
        will make sure that we reset to some usable default.
        """

        if not self._viewer is None:
            if not self._input_image is None:
                self._viewer.SetInput(self._input_image)
            else:
                self._viewer.SetInput(self._dummy_image_source.GetOutput())

            ii = self._viewer.GetInput()
            
            ii.UpdateInformation()
            ii.Update()
            range = ii.GetScalarRange()
            self._viewer.SetColorWindow(range[1] - range[0])
            self._viewer.SetColorLevel(0.5 * (range[1] + range[0]))
            
            icp = self._view_frame._image_control_panel
            icp.slider.SetRange(self._viewer.GetSliceMin(),
                                self._viewer.GetSliceMax())
            icp.slider.SetValue(self._viewer.GetSliceMin())
            
            #self._viewer.UpdateDisplayExtent()
            self._viewer.GetRenderer().ResetCamera()



