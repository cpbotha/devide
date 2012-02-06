# EmphysemaViewer by Corine Slagboom & Noeska Smit
# 
#
# Based on SkeletonAUIViewer:
# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

# skeleton of an AUI-based viewer module
# copy and modify for your own purposes.

# set to False for 3D viewer, True for 2D image viewer
IMAGE_VIEWER = True

# import the frame, i.e. the wx window containing everything
import EmphysemaViewerFrame
# and do a reload, so that the GUI is also updated at reloads of this
# module.
reload(EmphysemaViewerFrame)

from module_kits.misc_kit import misc_utils
from module_base import ModuleBase
from module_mixins import IntrospectModuleMixin
from comedi_utils import CMSliceViewer
from comedi_utils import SyncSliceViewers
import module_utils
import os
import sys
import traceback
import vtk
import wx

class EmphysemaViewer(IntrospectModuleMixin, ModuleBase):
    """Module to visualize lungemphysema in a CT scan. A lung mask is also needed. 

    EmphysemaViewer consists of a volume rendering and two linked slice-based views; one with the original data and one with an emphysema overlay. The volume rendering shows 3 
    contours: the lungedges and 2 different contours of emphysema; a normal one and a severe one. 

    There are two ways of setting the emphysema values. 
    - The first way is choosing the 'default' values, which are literature-based. They are set on -950 HU (emphysema) and -970 HU (severe). 
    - The other way is a computational way: The lowest 11% values, that are present in the data are marked as emphysema, the lowest 8,5% values are marked as severe emphysema.
    The theory behind this is the hypothesis that the histograms of emphysema patients differ from healthy people in a way that in emphysema patients there are relatively more  
    lower values present. In both ways you can finetune the values, or completely change them (if you want to). 

    After loading your image data and mask data, you can inspect the data and examine the severity of the emphysema of the patient. 

    Controls:
    LMB: The left mouse button can be used to rotate objects in the 3D scene, or to poll Houndsfield Units in areas of interest (click and hold to see the values)\n
    RMB: For the slice viewers, you can set the window and level values by clicking and holding the right mouse button in a slice and moving your mouse. You can see the current
    window and level values in the bottom of the viewer. Outside of the slice, this zooms the camera in and out\n
    MMB: The middle mouse button enables stepping through the slices if clicked and held in the center of the slice. When clicking on de edges of a slice, this re-orients the 
    entire slice. Outside of the slice, this pans the camera\n
    Scrollwheel: The scrollwheel can be used for zooming in and out of a scene, but also for sliceviewing if used with the CTRL- or SHIFT-key\n
    SHIFT: By holding the SHIFT-key, it is possible to use the mouse scrollwheel to scroll through the slices.\n
    CTRL: Holding the CTRL-key does the same, but enables stepping through the data in steps of 10 slices.\n
    """

    def __init__(self, module_manager):
        """Standard constructor.  All DeVIDE modules have these, we do
        the required setup actions.
        """

        # we record the setting here, in case the user changes it
        # during the lifetime of this model, leading to different
        # states at init and shutdown.
        self.IMAGE_VIEWER = IMAGE_VIEWER

	    # we need all this for our contours
        self.mask_data = None
        self.image_data = None
        self.lungVolume = None

        self.contour_severe_actor = vtk.vtkActor()
        self.contour_moderate_actor = vtk.vtkActor()
        self.contour_lungedge_actor = vtk.vtkActor()

        self.severe_mapper = vtk.vtkPolyDataMapper()
        self.severe_mapper.ScalarVisibilityOff()

        self.moderate_mapper = vtk.vtkPolyDataMapper()
        self.moderate_mapper.ScalarVisibilityOff()

        self.lung_mapper = vtk.vtkPolyDataMapper()
        self.lung_mapper.ScalarVisibilityOff()

        self.contour_severe_actor.SetMapper(self.severe_mapper)
        self.contour_severe_actor.GetProperty().SetColor(1,0,0)
        self.contour_severe_actor.GetProperty().SetOpacity(0.5)

        self.contour_moderate_actor.SetMapper(self.moderate_mapper)
        self.contour_moderate_actor.GetProperty().SetColor(0.5,0,1)
        self.contour_moderate_actor.GetProperty().SetOpacity(0.25)

        self.contour_lungedge_actor.SetMapper(self.lung_mapper)
        self.contour_lungedge_actor.GetProperty().SetColor(0.9,0.9,0.9)	
        self.contour_lungedge_actor.GetProperty().SetOpacity(0.1)

        ModuleBase.__init__(self, module_manager)

        # create the view frame
        self._view_frame = module_utils.instantiate_module_view_frame(
            self, self._module_manager, 
            EmphysemaViewerFrame.EmphysemaViewerFrame)
        # change the title to something more spectacular (or at least something non-default)
        self._view_frame.SetTitle('EmphysemaViewer')

        # create the necessary VTK objects: we only need a renderer,
        # the RenderWindowInteractor in the view_frame has the rest.
        self.ren = vtk.vtkRenderer()
        self.ren.SetBackground(0.5,0.5,0.5)
        self._view_frame.rwi.GetRenderWindow().AddRenderer(self.ren)

        self.ren.AddActor(self.contour_severe_actor)
        self.ren.AddActor(self.contour_moderate_actor)
        self.ren.AddActor(self.contour_lungedge_actor)

        self.ren2 = vtk.vtkRenderer()
        self.ren2.SetBackground(0.5,0.5,0.5)
        self._view_frame.overlay.GetRenderWindow().AddRenderer(self.ren2)
        self.slice_viewer1 = CMSliceViewer(self._view_frame.overlay, self.ren2)

        self.ren3 = vtk.vtkRenderer()
        self.ren3.SetBackground(0.5,0.5,0.5)
        self._view_frame.original.GetRenderWindow().AddRenderer(self.ren3)
        self.slice_viewer2 = CMSliceViewer(self._view_frame.original, self.ren3)
        
        self.slice_viewer3 = CMSliceViewer(self._view_frame.rwi, self.ren)
        

        self.sync = SyncSliceViewers()
        self.sync.add_slice_viewer(self.slice_viewer1)
        self.sync.add_slice_viewer(self.slice_viewer2)
        self.sync.add_slice_viewer2(self.slice_viewer3)

        # hook up all event handlers
        self._bind_events()

        # anything you stuff into self._config will be saved
        self._config.last_used_dir = ''

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
        FIXME: Still get a nasty X error :(
        """

        # with this complicated de-init, we make sure that VTK is 
        # properly taken care of
        self.ren.RemoveAllViewProps()
        self.ren2.RemoveAllViewProps()
        self.ren3.RemoveAllViewProps()

        # this finalize makes sure we don't get any strange X
        # errors when we kill the module.
        self.slice_viewer1.close()
        self.slice_viewer2.close()
        self.slice_viewer3.close()
        self._view_frame.rwi.GetRenderWindow().Finalize()
        self._view_frame.rwi.SetRenderWindow(None)
        self._view_frame.overlay.GetRenderWindow().Finalize()
        self._view_frame.overlay.SetRenderWindow(None)
        self._view_frame.original.GetRenderWindow().Finalize()
        self._view_frame.original.SetRenderWindow(None)
        del self._view_frame.rwi
        del self._view_frame.overlay
        del self._view_frame.original
        del self.slice_viewer3
        del self.slice_viewer2
        del self.slice_viewer1
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

    def create_volumerender(self, contourValueModerate, contourValueSevere):
        """Creates a volumerender of the masked data using iso-contour surfaces 
        created by the Marching Cubes algorithm at the specified contourvalues.
        """
        self._view_frame.SetStatusText("Creating Volumerender...")
        self.image_data
        mask = vtk.vtkImageMask()
        severeFraction = 0.10
        moderateFraction = 0.12
        
        # We only want to contour the lungs, so mask it
        mask.SetMaskInput(self.mask_data)
        mask.SetInput(self.image_data)
        mask.Update()
        self.lungVolume = mask.GetOutput()
        
        
        if contourValueModerate == 0 and contourValueSevere == 0: # This means we get to calculate the percentual values ourselves!
	        scalars = self.lungVolume.GetScalarRange()
	        range = scalars[1]-scalars[0]

	        contourValueSevere = scalars[0]+range*severeFraction
	        contourValueModerate = scalars[0]+range*moderateFraction

	        self._view_frame.upper_slider.SetValue(contourValueModerate)	
	        self._view_frame.lower_slider.SetValue(contourValueSevere)
	        self.create_overlay(contourValueModerate,contourValueSevere)

        # Create the contours
        self.adjust_contour(self.lungVolume, contourValueSevere, self.severe_mapper)
        self.adjust_contour(self.lungVolume, contourValueModerate, self.moderate_mapper)
        #self.adjust_contour(self.mask_data, 0.5, self.lung_mapper)
        self.create_lungcontour()

        # Set the camera to a nice view
        cam = self.ren.GetActiveCamera()
        cam.SetPosition(0,-100,0)
        cam.SetFocalPoint(0,0,0)
        cam.SetViewUp(0,0,1)
        self.ren.ResetCamera()
        self.render()
        self._view_frame.SetStatusText("Created Volumerender")

    def adjust_contour(self, volume, contourValue, mapper):
        """Adjust or create an isocontour using the Marching Cubes surface at the given 
        value using the given mapper
        """
    	self._view_frame.SetStatusText("Calculating new volumerender...")
    	contour = vtk.vtkMarchingCubes()
    	contour.SetValue(0,contourValue)
    	contour.SetInput(volume)
    	mapper.SetInput(contour.GetOutput())
    	mapper.Update()
    	self.render()
    	self._view_frame.SetStatusText("Calculated new volumerender")

    def create_lungcontour(self):
        """Create a lungcontour using the Marching Cubes algorithm and smooth the surface
        
        """
    	self._view_frame.SetStatusText("Calculating lungcontour...")
    	contourLung = vtk.vtkMarchingCubes()
    	contourLung.SetValue(0,1)
    	contourLung.SetInput(self.mask_data)

    	smoother = vtk.vtkWindowedSincPolyDataFilter()
    	smoother.SetInput(contourLung.GetOutput())
    	smoother.BoundarySmoothingOn()
    	smoother.SetNumberOfIterations(40)
    	smoother.Update()
    	self.lung_mapper.SetInput(smoother.GetOutput())
    	self.lung_mapper.Update()
    	self._view_frame.SetStatusText("Calculated lungcontour")

	
    def create_overlay(self, emphysemavalue, severeemphysemavalue):
        """Creates an overlay for the slice-based volume view
           0: no emphysema
           1: moderate emphysema
           2: severe emphysema
        """
        
    	self._view_frame.SetStatusText("Creating Overlay...")
    	mask = vtk.vtkImageMask()
    	mask2 = vtk.vtkImageMask()
    	threshold = vtk.vtkImageThreshold()
    	threshold2 = vtk.vtkImageThreshold()
    	math=vtk.vtkImageMathematics()
    
    	mask.SetInput(self.image_data)
    	mask.SetMaskInput(self.mask_data)
    
    	threshold.SetInput(mask.GetOutput())
    	threshold.ThresholdByLower(emphysemavalue)
    	threshold.SetOutValue(0)
    	threshold.SetInValue(1)

    	threshold2.SetInput(mask.GetOutput())
    	threshold2.ThresholdByLower(severeemphysemavalue)
    	threshold2.SetOutValue(1)
    	threshold2.SetInValue(2)

    	math.SetOperationToMultiply()
    	math.SetInput1(threshold.GetOutput())
    	math.SetInput2(threshold2.GetOutput())

    	math.Update()

    	overlay = math.GetOutput()
    	self.slice_viewer1.set_overlay_input(None)
    	self.slice_viewer1.set_overlay_input(overlay)
    	self.render()
    	self._view_frame.SetStatusText("Created Overlay")
    	

    def load_data_from_file(self, file_path):
        """Loads scanvolume data from file. Also sets the volume as input for the sliceviewers
        """
        self._view_frame.SetStatusText("Opening file: %s..." % (file_path))        
        filename = os.path.split(file_path)[1]
        fileBaseName =os.path.splitext(filename)[0]

        reader = vtk.vtkMetaImageReader()
        reader.SetFileName(file_path)
        reader.Update()
        self.image_data = reader.GetOutput()
        self.slice_viewer1.set_input(self.image_data)
        self.slice_viewer1.reset_camera()
        self.slice_viewer1.render()

        self.slice_viewer2.set_input(self.image_data)
        self.slice_viewer2.reset_camera()
        self.slice_viewer2.render()
        
        self.slice_viewer3.set_input(self.image_data)
        self.slice_viewer3.render()
        self.slice_viewer3.set_opacity(0.1)
        cam = self.ren.GetActiveCamera()
        cam.SetPosition(0,-100,0)
        cam.SetFocalPoint(0,0,0)
        cam.SetViewUp(0,0,1)
        self.ren.ResetCamera()
       
        if (self.mask_data) is not None: # We can start calculating the volumerender
	        self.create_volumerender(0,0)
        else:
	        self._view_frame.SetStatusText("Opened file")

    def load_mask_from_file(self, file_path):
        """Loads mask file
        """
        self._view_frame.SetStatusText( "Opening mask: %s..." % (file_path))        
        filename = os.path.split(file_path)[1]
        fileBaseName =os.path.splitext(filename)[0]

        reader = vtk.vtkMetaImageReader()
        reader.SetFileName(file_path)
        reader.Update()
        self.mask_data = reader.GetOutput()
        if (self.image_data) is not None:
	        self.create_volumerender(0,0)
        else:
	        self._view_frame.SetStatusText("Opened mask file")
	        
    def save_to_file(self, file_path):
        """Save data from main renderwindow (the contour one) to a PNG-file
        """
        w2i  = vtk.vtkWindowToImageFilter()
        w2i.SetInput(self._view_frame.rwi.GetRenderWindow()); 
        w2i.Update()
        writer = vtk.vtkPNGWriter()
        writer.SetInput(w2i.GetOutput())
        writer.SetFileName(file_path)
        writer.Update()
        result = writer.Write()
        if result == 0:
            self._view_frame.SetStatusText( "Saved file")
        else:
            self._view_frame.SetStatusText( "Saved file to: %s..." % (file_path))

    def _bind_events(self):
        """Bind wx events to Python callable object event handlers.
        """

        vf = self._view_frame
        vf.Bind(wx.EVT_MENU, self._handler_file_open,
                id = vf.id_file_open)
        vf.Bind(wx.EVT_MENU, self._handler_mask_open,
                id = vf.id_mask_open)
        vf.Bind(wx.EVT_MENU, self._handler_file_save,
                id = vf.id_mask_save)

        self._view_frame.button1.Bind(wx.EVT_BUTTON,
                self._handler_button1)
        self._view_frame.button2.Bind(wx.EVT_BUTTON,
                self._handler_button2)
        self._view_frame.button3.Bind(wx.EVT_BUTTON,
               self._handler_button3)
        self._view_frame.button4.Bind(wx.EVT_BUTTON,
               self._handler_button4)
        self._view_frame.button5.Bind(wx.EVT_BUTTON,
               self._handler_button5)
        self._view_frame.button6.Bind(wx.EVT_BUTTON,
               self._handler_button6)

        self._view_frame.upper_slider.Bind(wx.EVT_SCROLL_CHANGED, self._handler_slider1)
        self._view_frame.lower_slider.Bind(wx.EVT_SCROLL_CHANGED, self._handler_slider2)

    def _handler_button1(self, event):
        """Reset the camera of the main render window
        """
        self.ren.ResetCamera()
        self.render()

    def _handler_button2(self, event):
        """Reset all for the main render window
        """
        cam = self.ren.GetActiveCamera()
        cam.SetPosition(0,-100,0)
        cam.SetFocalPoint(0,0,0)
        cam.SetViewUp(0,0,1)
        self.ren.ResetCamera()
        self.render()

    def _handler_button3(self, event):
        """Reset the camera for the sliceviewers
        """
        self.slice_viewer1.reset_camera()
        self.slice_viewer2.reset_camera()
        self.render()

    def _handler_button4(self, event):
        """Reset all for the sliceviewers
        """
        self.slice_viewer1.reset_to_default_view(2)
        self.slice_viewer2.reset_to_default_view(2)
        orientations = [2, 0, 1]
        for i, ipw in enumerate(self.slice_viewer1.ipws):
                ipw.SetPlaneOrientation(orientations[i]) # axial
                ipw.SetSliceIndex(0)
        self.render()

        for i, ipw in enumerate(self.slice_viewer2.ipws):
                ipw.SetPlaneOrientation(orientations[i]) # axial
                ipw.SetSliceIndex(0)
        self.render()

    def _handler_button5(self, event):
        """Adjust the contourvalues to values recommended in literature
        """
        if self.lungVolume == None:
	        return
        else:
            self._view_frame.upper_slider.SetValue(-950)	
            self._view_frame.lower_slider.SetValue(-970)
            self.adjust_contour(self.lungVolume, -950, self.moderate_mapper)
            self.adjust_contour(self.lungVolume, -970, self.severe_mapper)
            self.create_overlay(-950,-970)

    def _handler_button6(self, event):
        """Adjust the contourvalues to values calculated from data
        """
        if self.lungVolume == None:
	        return
        else:
	        self.create_volumerender(0, 0)


    def _handler_file_open(self, event):
        """Handler for file opening
        """
        filters = 'Volume files (*.mhd)|*.mhd;'
        dlg = wx.FileDialog(self._view_frame, "Please choose a CT-thorax file", self._config.last_used_dir, "", filters, wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:            
            filename=dlg.GetFilename()
            self._config.last_used_dir=dlg.GetDirectory()
            full_file_path = "%s/%s" % (self._config.last_used_dir, filename)
            self.load_data_from_file(full_file_path)
        dlg.Destroy()

    def _handler_mask_open(self, event):
        """Handler for mask opening
        """
        filters = 'Mask files (*.mhd;#.mha)|*.mhd;*mha;'
        dlg = wx.FileDialog(self._view_frame, "Please choose a CT-thorax mask file", self._config.last_used_dir, "", filters, wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:            
            filename=dlg.GetFilename()
            self._config.last_used_dir=dlg.GetDirectory()
            full_file_path = "%s/%s" % (self._config.last_used_dir, filename)
            self.load_mask_from_file(full_file_path)
        dlg.Destroy()

    def _handler_file_save(self, event):
        """Handler for filesaving
        """
        self._view_frame.SetStatusText( "Saving file...")         

        filters = 'png file (*.png)|*.png'
        dlg = wx.FileDialog(self._view_frame, "Choose a destination", self._config.last_used_dir, "", filters, wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            filename=dlg.GetFilename()
            self._config.last_used_dir=dlg.GetDirectory()
            file_path = "%s/%s" % (self._config.last_used_dir, filename)
            self.save_to_file(file_path)
        dlg.Destroy()
        self._view_frame.SetStatusText( "Saved file")

    def _handler_slider1(self, event):
        """Handler for slider adjustment (Severe emphysema)
        """
        if self.lungVolume == None:
	    	return
        else:
        	contourValue = self._view_frame.upper_slider.GetValue()
    		self.adjust_contour(self.lungVolume, contourValue, self.moderate_mapper)
    		self.create_overlay(contourValue, self._view_frame.lower_slider.GetValue())

    def _handler_slider2(self, event):
        """Handler for slider adjustment (Moderate emphysema)
        """
        if self.lungVolume == None:
	    	return
        else:        
	    	contourValue = self._view_frame.lower_slider.GetValue()
	    	self.adjust_contour(self.lungVolume, contourValue, self.severe_mapper)
	    	self.create_overlay(self._view_frame.upper_slider.GetValue(),contourValue)

    def render(self):
        """Method that calls Render() on the embedded RenderWindow.
        Use this after having made changes to the scene.
        """
        self._view_frame.render()
        self.slice_viewer1.render()
