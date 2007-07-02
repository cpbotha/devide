from moduleBase import moduleBase
from moduleMixins import introspectModuleMixin
import moduleUtils
import Measure2DFrame
reload(Measure2DFrame)

import vtk
import wx

class Measure2D(introspectModuleMixin, moduleBase):

    def __init__(self, module_manager):
        moduleBase.__init__(self, module_manager)

        self._view_frame = None
        self._viewer = None
        self._input_image = None
        
        self._widgets = []
        
        self.view()
        
    def close(self):
        if self._view_frame is not None:
            self._view_frame.close()
            
    def view(self):
        if self._view_frame is None:
            self._view_frame = moduleUtils.instantiateModuleViewFrame(
                self, self._moduleManager, Measure2DFrame.Measure2DFrame)

            self._create_vtk_pipeline()
            
            # now link up all event handlers
            self._bind_events()
            
        self._view_frame.Show()
        self._view_frame.Raise()
        
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

            self._viewer = vtk.vtkImageViewer2()
            self._view_frame._rwi.SetRenderWindow(self._viewer.GetRenderWindow())
            self._viewer.SetupInteractor(self._view_frame._rwi)
            self._viewer.GetRenderer().SetBackground(0.3,0.3,0.3)            
            

    def _handler_new_measurement_button(self, event):
        handle = vtk.vtkPointHandleRepresentation2D()
        handle.GetProperty().SetColor(1,0,0)
        rep = vtk.vtkDistanceRepresentation2D()
        rep.SetHandleRepresentation(handle)

        rep.GetAxis().SetNumberOfMinorTicks(4)
        rep.GetAxis().SetTickLength(9)
        rep.GetAxis().SetTitlePosition(0.2)
        
        w = vtk.vtkDistanceWidget()
        w.SetInteractor(self._view_frame._rwi)        
        w.CreateDefaultRepresentation()
        w.SetRepresentation(rep)
        
        w.On()

        self._widgets.append(w)
            
    def _handler_slice_slider(self, event):
        if not self._input_image is None:
            val = self._view_frame._image_control_panel.slider.GetValue()
            self._viewer.SetSlice(val)
                
    def _setup_new_image(self):
        """Based on the current self._input_image and the viewer, this thing will make sure
        that we reset to some usable default.
        """
        
        if not self._input_image is None and not self._viewer is None:
            self._viewer.SetInput(self._input_image)
            
            self._input_image.UpdateInformation()
            self._input_image.Update()
            range = self._input_image.GetScalarRange()
            self._viewer.SetColorWindow(range[1] - range[0])
            self._viewer.SetColorLevel(0.5 * (range[1] + range[0]))
            
            
            self._input_image.UpdateInformation()
            self._input_image.Update()
            range = self._input_image.GetScalarRange()
            self._viewer.SetColorWindow(range[1] - range[0])
            self._viewer.SetColorLevel(0.5 * (range[1] + range[0]))
            
            icp = self._view_frame._image_control_panel
            icp.slider.SetRange(self._viewer.GetSliceMin(),
                                self._viewer.GetSliceMax())
            icp.slider.SetValue(self._viewer.GetSliceMin())
            
            #self._viewer.UpdateDisplayExtent()
            self._viewer.GetRenderer().ResetCamera()
            self._view_frame._rwi.Render()

            
