from wxPython._controls import wxLIST_MASK_STATE
from wxPython._controls import wxLIST_STATE_SELECTED
import os.path
# Modified by Francois Malan, LUMC / TU Delft
# December 2009
#
# based on the SkeletonAUIViewer:
# skeleton of an AUI-based viewer module
# Copyright (c) Charl P. Botha, TU Delft.

# set to False for 3D viewer, True for 2D image viewer
IMAGE_VIEWER = False

# import the frame, i.e. the wx window containing everything
import MaskComBinarFrame
# and do a reload, so that the GUI is also updated at reloads of this
# module.
reload(MaskComBinarFrame)

from module_base import ModuleBase
from module_mixins import IntrospectModuleMixin
import module_utils
import os
import vtk
import itk
import wx
import copy
import subprocess
#import numpy as np

from OverlaySliceViewer import OverlaySliceViewer

class Mask(object):
    def __init__(self, name, file_path, image_data):
        self.name = name
        self.file_path = file_path
        self.data = image_data

#    def deepcopy(self):
#        return Mask(self.name, self.file_path, self.data.DeepCopy())

class MaskComBinar(IntrospectModuleMixin, ModuleBase):
    def __init__(self, module_manager):
        """Standard constructor.  All DeVIDE modules have these, we do
        the required setup actions.
        """

        # we record the setting here, in case the user changes it
        # during the lifetime of this model, leading to different
        # states at init and shutdown.
        self.IMAGE_VIEWER = IMAGE_VIEWER

        ModuleBase.__init__(self, module_manager)        

        # create the view frame
        self._view_frame = module_utils.instantiate_module_view_frame(
            self, self._module_manager, 
            MaskComBinarFrame.MaskComBinarFrame)
        # change the title to something more spectacular

        self._view_frame.SetTitle('Mask ComBinar \t (c) Francois Malan, LUMC & TU Delft')

        #initialise data structures
        self._init_data_structures()
        
        self._init_2d_render_window()
        self._init_3d_render_window()

        self.reset_camera_on_mask_display = True
        self.first_save_warning = True

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

        #This tool can be used for introspection of wx components
        #

    def _init_2d_render_window(self):
        #create the necessary VTK objects for the 2D window. We use Charl's CMSliceViewer
        #which defines all the nice goodies we'll need
        self.ren2d = vtk.vtkRenderer()
        self.ren2d.SetBackground(0.4,0.4,0.4)
        self.slice_viewer = OverlaySliceViewer(self._view_frame.rwi2d, self.ren2d)
        self._view_frame.rwi2d.GetRenderWindow().AddRenderer(self.ren2d)
        self.slice_viewer.add_overlay('a', [0, 0, 1, 1]) #Blue for selection A
        self.slice_viewer.add_overlay('b', [1, 0, 0, 1]) #Red for selection B
        self.slice_viewer.add_overlay('intersect', [1, 1, 0, 1]) #Yellow for for intersection

    def _init_3d_render_window(self):
        # create the necessary VTK objects for the 3D window: we only need a renderer,
        # the RenderWindowInteractor in the view_frame has the rest.
        self.ren3d = vtk.vtkRenderer()
        self.ren3d.SetBackground(0.6,0.6,0.6)
        self._view_frame.rwi3d.GetRenderWindow().AddRenderer(self.ren3d)

    def _init_data_structures(self):
        self.opacity_3d = 0.5
        self.rgb_blue = [0,0,1]
        self.rgb_red =  [1,0,0]
        self.rgb_yellow = [1,1,0]

        self.masks = {}
        self.surfaces = {}   #This prevents recomputing surface meshes
        self.actors3d = {}
        self.rendered_masks_in_a = set()
        self.rendered_masks_in_b = set()
        self.rendered_overlap = False

    def _load_mask_from_file(self, file_path):
        print "Opening file: %s" % (file_path)
        filename = os.path.split(file_path)[1]
        reader = None
        extension = os.path.splitext(filename)[1]
        if extension == '.vti':       # VTI
            reader = vtk.vtkXMLImageDataReader()
        elif extension == '.mha':     # MHA
            reader = vtk.vtkMetaImageReader()
        else:
            self._view_frame.dialog_error('Unknown file extension: %s' % extension, 'Unable to handle extension')
            return

        reader.SetFileName(file_path)
        reader.Update()

        result = vtk.vtkImageData()
        result.DeepCopy(reader.GetOutput())
        return result

    def load_binary_mask_from_file(self, file_path):
        mask_image_data = self._load_mask_from_file(file_path)
        filename = os.path.split(file_path)[1]
        fileBaseName =os.path.splitext(filename)[0]
        mask = Mask(fileBaseName, file_path, mask_image_data)
        self.add_mask(mask)

    def load_multi_mask_from_file(self, file_path):
        mask_image_data = self._load_mask_from_file(file_path)
        filename = os.path.split(file_path)[1]
        fileBaseName =os.path.splitext(filename)[0]

        #Now we have to create a separate mask for each integer level.
        accumulator = vtk.vtkImageAccumulate()
        accumulator.SetInput(mask_image_data)
        accumulator.Update()
        max_label = int(accumulator.GetMax()[0])

        #We assume all labels to have positive values.
        for i in range(1,max_label+1):
            label_data = self._threshold_image(mask_image_data, i, i)
            new_name = '%s_%d' % (fileBaseName, i)
            mask = Mask(new_name, file_path, label_data)
            self.add_mask(mask)

    def save_mask_to_file(self, mask_name, file_path):
        if os.path.exists(file_path):
            result = self._view_frame.dialog_yesno("%s already exists! \nOverwrite?" % file_path,"File already exists")
            if result == False:
                print 'Skipped writing %s' % file_path
                return    #skip this file if overwrite is denied

        mask = self.masks[mask_name]
        mask.file_path = file_path

        filename = os.path.split(file_path)[1]

        writer = None
        extension = os.path.splitext(filename)[1]
        if extension == '.vti':       # VTI
            writer = vtk.vtkXMLImageDataWriter()
        elif extension == '.mha':     # MHA
            print 'Attempting to create an mha writer. This has failed in the past (?)'
            writer = vtk.vtkMetaImageWriter()
            writer.SetCompression(True)
        else:
            self._view_frame.dialog_error('Unknown file extension: %s' % extension, 'Unable to handle extension')
            return
        
        writer.SetInput(mask.data)
        writer.SetFileName(mask.file_path)
        writer.Update()
        result = writer.Write()
        if result == 0:
            self._view_frame.dialog_error('Error writing %s' % filename, 'Error writing file')
            print 'ERROR WRITING FILE!!!'
        else:
            self._view_frame.dialog_info('Successfully wrote %s' % filename, 'Success')
            print 'Successfully wrote %s' % file_path
        
    def add_mask(self, mask):
        [accept, name] = self._view_frame.dialog_inputtext('Please choose a name for the new mask','Choose a name', mask.name)
        if accept:
            mask.name = name
            if self.masks.has_key(name):
                i=1
                new_name = '%s%d' % (name, i)

                while self.masks.has_key(new_name):
                    i += 1
                    new_name = '%s%d' % (mask.name, i)
                mask.name = new_name
            self.masks[mask.name] = mask
            self._view_frame.add_mask(mask.name)

    def delete_masks(self, mask_names):
        temp = mask_names.copy()
        if len(mask_names) > 0:
            mask_names_str = mask_names.pop()
            while len(mask_names) > 0:
                mask_names_str = mask_names_str + ',%s' % mask_names.pop()

            mask_names = temp
            if self._view_frame.dialog_yesno('Are you sure you want to delete the following masks: %s' % mask_names_str, 'Delete masks?'):
                for mask_name in mask_names:
                    print 'deleting mask: %s' % mask_name
                    if self.masks.has_key(mask_name):
                        self.masks.pop(mask_name)                        
                        self._view_frame.delete_mask(mask_name)
                    else:
                        self._view_frame.dialog_error('Mask "%s" not found in internal mask list!' % mask_name, 'Mask not found')
                if len(self.masks) == 0:    #If there are no masks left we disable the 2D viewer's pickable plane
                    self.slice_viewer.set_input(0, None)


    def close(self):
        """Clean-up method called on all DeVIDE modules when they are
        deleted.
        """
        
        # with this complicated de-init, we make sure that VTK is 
        # properly taken care of
        self.ren2d.RemoveAllViewProps()
        self.ren3d.RemoveAllViewProps()
        # this finalize makes sure we don't get any strange X
        # errors when we kill the module.
        self._view_frame.rwi2d.GetRenderWindow().Finalize()
        self._view_frame.rwi2d.SetRenderWindow(None)
        del self._view_frame.rwi2d

        self._view_frame.rwi3d.GetRenderWindow().Finalize()
        self._view_frame.rwi3d.SetRenderWindow(None)
        del self._view_frame.rwi3d
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
        # your output data.
        pass

    def execute_module(self):
        # when it's your turn to execute as part of a network
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

    def _update_3d_masks(self, id, removed, added):
        rgb_colour = [0,0,0]        
        if id == 'a':
            rgb_colour = self.rgb_blue
        elif id == 'b':
            rgb_colour = self.rgb_red

        for name in removed:
            key = id + name
            self.ren3d.RemoveActor(self.actors3d[key])
        self.render()

        for name in added:
            self._render_3d_mask(id, name, rgb_colour, self.opacity_3d)

    def _update_3d_masks_overlapping(self, mask_a, mask_b, mask_intersect):
        self._clear_3d_window()
        self._render_3d_data('a_not_b', mask_a.data, self.rgb_blue, self.opacity_3d)
        self._render_3d_data('b_not_a', mask_b.data, self.rgb_red, self.opacity_3d)
        self._render_3d_data('a_and_b', mask_intersect.data, self.rgb_yellow, self.opacity_3d)

    def _clear_3d_window(self):
        for actor in self.actors3d.values():
            self.ren3d.RemoveActor(actor)
        self.ren3d.Clear()
        self.rendered_masks_in_a = set()
        self.rendered_masks_in_b = set()
        self.rendered_overlap = False

    def _render_2d_mask(self, id, mask):
        mask_data = None
        if mask != None:
            mask_data = mask.data
        self.slice_viewer.set_input(id, mask_data)
        if self.reset_camera_on_mask_display:
            self.slice_viewer.reset_camera()
        #self.slice_viewer.reset_to_default_view(2)
        self.slice_viewer.render()

    def _render_3d_mask(self, id, name, rgb_colour, opacity):
        """Add the given mask to the 3D display window.
           An iso-surface of colour rgb_colour is rendered at value = 1.
        """
        surface = None
        mask = self.masks[name]
        if not self.surfaces.has_key(name):
            surface_creator = vtk.vtkDiscreteMarchingCubes()
            surface_creator.SetInput(mask.data)
            surface_creator.Update()
            surface = surface_creator.GetOutput()
            self.surfaces[name] = surface
        else:
            surface = self.surfaces[name]

        m = vtk.vtkPolyDataMapper()
        m.SetInput(surface)
        m.ScalarVisibilityOff()
        actor = vtk.vtkActor()
        actor.SetMapper(m)
                
        actor.SetPosition(mask.data.GetOrigin())
        actor.GetProperty().SetColor(rgb_colour)
        actor.GetProperty().SetOpacity(opacity)
        #actor.GetProperty().SetInterpolationToFlat()        

        self.ren3d.AddActor(actor)
        self.actors3d[id+name] = actor
        
        if self.reset_camera_on_mask_display:
            self.ren3d.ResetCamera()

        self.render()

    def _render_3d_data(self, id, data, rgb_colour, opacity):
        """Add the given mask to the 3D display window.
           An iso-surface of colour rgb_colour is rendered at value = 1.
        """
        surface_creator = vtk.vtkDiscreteMarchingCubes()
        surface_creator.SetInput(data)
        surface_creator.Update()
        surface = surface_creator.GetOutput()

        m = vtk.vtkPolyDataMapper()
        m.SetInput(surface)
        m.ScalarVisibilityOff()
        actor = vtk.vtkActor()
        actor.SetMapper(m)

        actor.SetPosition(data.GetOrigin())
        actor.GetProperty().SetColor(rgb_colour)
        actor.GetProperty().SetOpacity(opacity)
        #actor.GetProperty().SetInterpolationToFlat()

        self.ren3d.AddActor(actor)
        self.actors3d[id] = actor

        if self.reset_camera_on_mask_display:
            self.ren3d.ResetCamera()

        self.render()


    def _bind_events(self):
        """Bind wx events to Python callable object event handlers.
        """

        vf = self._view_frame
        vf.Bind(wx.EVT_MENU, self._handler_open_binary_mask,
                id = vf.id_open_binary_mask)

        vf.Bind(wx.EVT_MENU, self._handler_open_multi_mask,
                id = vf.id_open_multi_mask)

        vf.Bind(wx.EVT_MENU, self._handler_open_mask_dir,
                id = vf.id_open_mask_dir)

        vf.Bind(wx.EVT_MENU, self._handler_save_mask,
                id = vf.id_save_mask)

        vf.Bind(wx.EVT_MENU, self._handler_close,
                id = vf.id_quit)

        vf.Bind(wx.EVT_MENU, self._handler_introspect,
                id = vf.id_introspect)

        self._view_frame.reset_cam2d_button.Bind(wx.EVT_BUTTON,
                self._handler_reset_cam2d_button)

        self._view_frame.reset_cam3d_button.Bind(wx.EVT_BUTTON,
                self._handler_reset_cam3d_button)
        self._view_frame.clear_selection_button.Bind(wx.EVT_BUTTON,
                self._handler_clear_selection_button)

        self._view_frame.list_ctrl_maskA.Bind(wx.EVT_LIST_ITEM_SELECTED, self._handler_listctrl)
        self._view_frame.list_ctrl_maskA.Bind(wx.EVT_LIST_ITEM_DESELECTED, self._handler_listctrl)
        self._view_frame.list_ctrl_maskB.Bind(wx.EVT_LIST_ITEM_SELECTED, self._handler_listctrl)
        self._view_frame.list_ctrl_maskB.Bind(wx.EVT_LIST_ITEM_DESELECTED, self._handler_listctrl)

        
        self._view_frame.list_ctrl_maskA.Bind(wx.EVT_LIST_KEY_DOWN, self._handler_delete_mask_a)
        self._view_frame.list_ctrl_maskB.Bind(wx.EVT_LIST_KEY_DOWN, self._handler_delete_mask_b)

        #Mask operations
        self._view_frame.mask_join_button.Bind(wx.EVT_BUTTON, self._handler_mask_join)
        self._view_frame.mask_subtract_button.Bind(wx.EVT_BUTTON, self._handler_mask_subtract)
        self._view_frame.mask_intersect_button.Bind(wx.EVT_BUTTON, self._handler_mask_intersect)

        self._view_frame.mask_align_metadata_button.Bind(wx.EVT_BUTTON, self._handler_align_masks_metadata)
        self._view_frame.mask_align_icp_button.Bind(wx.EVT_BUTTON, self._handler_align_masks_icp)
        self._view_frame.split_disconnected_button.Bind(wx.EVT_BUTTON, self._handler_split_disconnected)

        #Mask diagnostics
        self._view_frame.test_all_dimensions_button.Bind(wx.EVT_BUTTON, self._handler_test_all_dimensions)
        self._view_frame.test_selected_dimensions_button.Bind(wx.EVT_BUTTON, self._handler_test_selected_dimensions)
        self._view_frame.test_all_intersections_button.Bind(wx.EVT_BUTTON, self._handler_test_all_intersections)
        self._view_frame.test_selected_intersections_button.Bind(wx.EVT_BUTTON, self._handler_test_selected_intersections)

        #Mask metrics
        self._view_frame.volume_button.Bind(wx.EVT_BUTTON, self._handler_compute_volume)
        self._view_frame.dice_coefficient_button.Bind(wx.EVT_BUTTON, self._handler_compute_dice_coefficient)
        self._view_frame.hausdorff_distance_button.Bind(wx.EVT_BUTTON, self._handler_compute_hausdorff_distance)
        self._view_frame.mean_hausdorff_distance_button.Bind(wx.EVT_BUTTON, self._handler_compute_mean_hausdorff_distance)

	#self._view_frame.Bind(wx.EVT_SLIDER, self._handler_slider_update)

    def _handler_reset_cam2d_button(self, event):
        #self.slice_viewer.reset_camera()
        self.slice_viewer.reset_to_default_view(2)
        self.render()

    def _handler_reset_cam3d_button(self, event):
        self.ren3d.ResetCamera()
        self.render()

    def _handler_clear_selection_button(self, event):
        self._view_frame.clear_selections()
        self._clear_3d_window()

        self.slice_viewer.set_input(0, None)
        self.slice_viewer.set_input('a', None)
        self.slice_viewer.set_input('b', None)
        self.slice_viewer.set_input('intersect', None)
        self.render()

    def _handler_delete_mask_a(self, event):
        '''Handler for deleting an mask from either of the two lists (acts on both)'''
        if event.KeyCode == 127: #This is the keycode for "delete"
            names_a = self._view_frame.get_selected_mask_names_a()
            if len(names_a) > 0:
                self.delete_masks(names_a)

    def _handler_delete_mask_b(self, event):
        '''Handler for deleting an mask from either of the two lists (acts on both)'''
        if event.KeyCode == 127: #This is the keycode for "delete"
            names_b = self._view_frame.get_selected_mask_names_b()
            if len(names_b) > 0:
                self.delete_masks(names_b)

    def _handler_listctrl(self, event):
        """Mask is selected or deselected in listcontrol A"""
        if self.rendered_overlap:
            self._clear_3d_window()
            self.rendered_overlap = False

        names_a = self._view_frame.get_selected_mask_names_a()
        names_b = self._view_frame.get_selected_mask_names_b()
        new_in_a = set()
        new_in_b = set()
        gone_from_a = set()
        gone_from_b = set()
        #Check what has changed
        for name in names_a:
            if not name in self.rendered_masks_in_a:
                new_in_a.add(name)
        for name in self.rendered_masks_in_a:
            if not name in names_a:
                gone_from_a.add(name)
        #Update the list of selected items
        self.rendered_masks_in_a = names_a

        for name in names_b:
            if not name in self.rendered_masks_in_b:
                new_in_b.add(name)
        for name in self.rendered_masks_in_b:
            if not name in names_b:
                gone_from_b.add(name)
        #Update the list of selected items
        self.rendered_masks_in_b = names_b

        overlap = None
        union_masks_a = None
        union_masks_b = None
        if (len(gone_from_a) > 0) or (len(new_in_a) > 0) or (len(gone_from_b) > 0) or (len(new_in_b) > 0):
            union_masks_a = self.compute_mask_union(names_a)
            union_masks_b = self.compute_mask_union(names_b)
            self._render_2d_mask('a',union_masks_a)
            self._render_2d_mask('b',union_masks_b)
            overlap = self._logical_intersect_masks(union_masks_a, union_masks_b)
            if self._is_empty_mask(overlap):
                overlap = None
            self._render_2d_mask('intersect',overlap)

        if overlap == None:
            #We don't need to render any custom mask - only a list of existing selected masks
            self._update_3d_masks('a', gone_from_a, new_in_a)
            self._update_3d_masks('b', gone_from_b, new_in_b)
        else:
            #We require a more expensive custom render to show overlapping areas in 3D
            a_not_b = self._logical_subtract_masks(union_masks_a, overlap)
            b_not_a = self._logical_subtract_masks(union_masks_b, overlap)
            self._update_3d_masks_overlapping(a_not_b, b_not_a, overlap)
            self.rendered_masks_in_a = {}
            self.rendered_masks_in_b = {}
            self.rendered_overlap = True

    def _handler_open_binary_mask(self, event):
        """Opens a binary mask file"""
        filters = 'Mask files (*.vti;*.mha)|*.vti;*.mha'
        dlg = wx.FileDialog(self._view_frame, "Choose a binary mask file", self._config.last_used_dir, "", filters, wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:            
            filename=dlg.GetFilename()
            self._config.last_used_dir=dlg.GetDirectory()
            full_file_path = "%s\\%s" % (self._config.last_used_dir, filename)
            self.load_binary_mask_from_file(full_file_path)
        dlg.Destroy()

    def _handler_open_multi_mask(self, event):
        """Opens an integer-labeled multi-material mask file"""
        filters = 'Mask files (*.vti;*.mha)|*.vti;*.mha'
        dlg = wx.FileDialog(self._view_frame, "Choose a multi-label mask file", self._config.last_used_dir, "", filters, wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename=dlg.GetFilename()
            self._config.last_used_dir=dlg.GetDirectory()
            full_file_path = "%s\\%s" % (self._config.last_used_dir, filename)
            self.load_multi_mask_from_file(full_file_path)
        dlg.Destroy()

    def _handler_open_mask_dir(self, event):
        """Opens all masks in a given directory"""
        dlg = wx.DirDialog(self._view_frame, "Choose a directory containing masks", self._config.last_used_dir)
        if dlg.ShowModal() == wx.ID_OK:
            dir_name=dlg.GetPath()
            self._config.last_used_dir=dir_name

            all_files = os.listdir(dir_name)
            #First we set up actor list of files with the correct extension
            file_list = []
            source_ext = '.vti'
            for f in all_files:
                file_name = os.path.splitext(f)
                if file_name[1] == source_ext:
                    file_list.append(f)

            for filename in file_list:
                full_file_path = "%s\\%s" % (dir_name, filename)
                self.load_binary_mask_from_file(full_file_path)
        dlg.Destroy()
        print 'Done!'

    def _handler_save_mask(self, event):
        """Saves a mask file"""
        if self.test_single_mask_selection():
            names_a = self._view_frame.get_selected_mask_names_a()
            names_b = self._view_frame.get_selected_mask_names_b()

            mask_name = ''
            if len(names_b) == 1:
                mask_name = names_b.pop()
            else:
                mask_name = names_a.pop()

            filters = 'Mask files (*.vti;*.mha)|*.vti;*.mha'
            dlg = wx.FileDialog(self._view_frame, "Choose a destination", self._config.last_used_dir, "", filters, wx.SAVE)
            if dlg.ShowModal() == wx.ID_OK:
                filename=dlg.GetFilename()
                self._config.last_used_dir=dlg.GetDirectory()
                file_path = "%s\\%s" % (self._config.last_used_dir, filename)
                self.save_mask_to_file(mask_name, file_path)
            dlg.Destroy()
            print 'Done!'

    def _handler_align_masks_metadata(self, event):
        """Aligns two masks by copying metadata from the first to the second (origin, spacing, extent, wholeextent)
           As always, creates a new mask in the list of masks as output.
        """
        if self.test_single_mask_pair_selection():
            #We know that there is only a single mask selected in each of A and B, therefor we only index the 0th element in each
            names_a = self._view_frame.get_selected_mask_names_a()
            names_b = self._view_frame.get_selected_mask_names_b()
            maskA = self.masks[names_a.pop()]
            maskB = self.masks[names_b.pop()]

            mask_data = vtk.vtkImageData()
            mask_data.DeepCopy(maskB.data)

            mask_data.SetOrigin(maskA.data.GetOrigin())
            mask_data.SetExtent(maskA.data.GetExtent())
            mask_data.SetWholeExtent(maskA.data.GetWholeExtent())
            mask_data.SetSpacing(maskA.data.GetSpacing())

            mask = Mask('%s_a' % maskB.name, maskB.file_path, mask_data)
            self.add_mask(mask)

    def _handler_split_disconnected(self, event):
        """Splits the selected mask into disconnected regions"""
        if self.test_single_mask_selection():
            name_set = self._view_frame.get_selected_mask_names_a()
            if len(name_set) == 0:
                name_set = self._view_frame.get_selected_mask_names_b()
            
            mask = self.masks[names_set.pop()]
            self._split_disconnected_objects(mask)

    def _handler_align_masks_icp(self, event):
        """Aligns two masks by using the Iterative Closest Point algorithm (rigid transformation)
           As always, creates a new mask in the list of masks as output.
        """
        if self.test_single_mask_pair_selection():
            #We know that there is only a single mask selected in each of A and B, therefor we only index the 0th element in each
            names_a = self._view_frame.get_selected_mask_names_a()
            names_b = self._view_frame.get_selected_mask_names_b()
            maskA = self.masks[names_a.pop()]
            maskB = self.masks[names_b.pop()]

            #We need meshes (polydata) as input to the ICP algorithm
            meshA = None
            meshB = None
            #actually this should never happen, but let's keep it for making double sure
            if not self.surfaces.has_key(maskA.name): 
                surface_creator_A = vtk.vtkDiscreteMarchingCubes()
                surface_creator_A.SetInput(maskA.data)
                surface_creator_A.Update()
                meshA = surface_creator_A.GetOutput()
            else:
                meshA = self.surfaces[maskA.name]

            #actually this should never happen, but let's keep it for making double sure
            if not self.surfaces.has_key(maskB.name):
                surface_creator_B = vtk.vtkDiscreteMarchingCubes()
                surface_creator_B.SetInput(maskB.data)
                surface_creator_B.Update()
                meshB = surface_creator_B.GetOutput()
            else:
                meshB = self.surfaces[maskB.name]

            icp = vtk.vtkIterativeClosestPointTransform()
            icp.SetMaximumNumberOfIterations(50)

            icp.SetSource(meshA)
            icp.SetTarget(meshB)

            print 'Executing ICP alorithm'
            icp.Update()            
            del meshA, meshB

            reslicer = vtk.vtkImageReslice()
            reslicer.SetInterpolationModeToNearestNeighbor()
            #reslicer.SetInterpolationModeToCubic()
            reslicer.SetInput(maskB.data)
            reslicer.SetResliceTransform(icp)
            reslicer.Update()
            del maskA, maskB
            
            result = vtk.vtkImageData()
            result.DeepCopy(reslicer.GetOutput())
            self.add_mask(Mask('Aligned','',result))

    def _handler_compute_volume(self, event):
        """Computes the volume of of mask A (in milliliters)"""
        if self.test_valid_mask_selection_a_only():
            names_a = self._view_frame.get_selected_mask_names_a()
            union_masksA = self.compute_mask_union(names_a)

            spacing = union_masksA.data.GetSpacing()
            voxel_volume = spacing[0] * spacing[1] * spacing[2]
            
            accumulator = vtk.vtkImageAccumulate()
            accumulator.SetInput(union_masksA.data)
            accumulator.Update()
            nonzero_count = accumulator.GetMean()[0] * accumulator.GetVoxelCount()

            volume = voxel_volume * nonzero_count / 1000.0

            print "Volume = %.2f ml" % (volume)
            copy_to_clipboard = self._view_frame.dialog_yesno('Volume = %f ml\n\nCopy to clipboard?' % volume, 'Volume = %.1f%% ml' % (volume))
            if copy_to_clipboard:
                self._view_frame.copy_text_to_clipboard('%f' % volume)

    def _is_empty_mask(self, mask):
        if mask == None:
            return True
        else:
            accumulator = vtk.vtkImageAccumulate()
            accumulator.SetInput(mask.data)
            accumulator.Update()
            return accumulator.GetMax()[0] == 0

    def _handler_compute_dice_coefficient(self, event):
        """Computes the Dice coefficient between selections in A and B
        Implementation from Charl's coderunner code"""
        if self.test_valid_mask_selection_a_and_b():
            names_a = self._view_frame.get_selected_mask_names_a()
            names_b = self._view_frame.get_selected_mask_names_b()
            union_masksA = self.compute_mask_union(names_a)
            union_masksB = self.compute_mask_union(names_b)

            # Given two binary volumes, this CodeRunner will implement
            # the percentage volume overlap.  This is useful for
            # doing validation with ground truth / golden standard /
            # manually segmented volumes.  This is also called the Dice
            # coefficient and ranges from 0.0 to 1.0.

            # interesting paper w.r.t. segmentation validation:
            # Valmet: A new validation tool for assessing and improving 3D object segmentation

            # basic idea:
            # threshold data (so we have >0 == 1 and everything else 0)
            # then histogram into two bins.

            threshes = []

            for _ in range(2):
                t = vtk.vtkImageThreshold()
                threshes.append(t)
                # anything equal to or lower than 0.0 will be "In"
                t.ThresholdByLower(0.0)
                # <= 0 -> 0
                t.SetInValue(0)
                # > 0 -> 1
                t.SetOutValue(1)
                t.SetOutputScalarTypeToUnsignedChar()

            # have to stuff all components into one image
            iac = vtk.vtkImageAppendComponents()
            iac.SetInput(0, threshes[0].GetOutput())
            iac.SetInput(1, threshes[1].GetOutput())

            # generate 2 by 2 matrix (histogram)
            ia = vtk.vtkImageAccumulate()
            ia.SetInput(iac.GetOutput())
            ia.SetComponentExtent(0,1, 0,1, 0,0)

            threshes[0].SetInput(union_masksA.data)
            threshes[1].SetInput(union_masksB.data)
            ia.Update()

            iasc = ia.GetOutput().GetPointData().GetScalars()
            cells = [0] * 4
            for i in range(4):
                cells[i] = iasc.GetTuple1(i)

            # tuple 0: not in actor, not in b
            # tuple 1: in actor, not in b
            # tuple 2: in b, not in actor
            # tuple 3: in actor, in b

            # percentage overlap: (a intersect b) / (a union b)

            dice_coeff = (2 * cells[3] / (2* cells[3] + cells[1] + cells[2]))
            
            print "Dice Coefficiet = %.2f" % (dice_coeff)
            copy_to_clipboard = self._view_frame.dialog_yesno('Dice coefficient = %f\n\nCopy to clipboard?' % dice_coeff, '%.1f%% overlap' % (100*dice_coeff))
            if copy_to_clipboard:
                self._view_frame.copy_text_to_clipboard('%f' % dice_coeff)


    def _compute_hausdorff_distances(self, maskA, maskB):
        """
        Computes the Hausdorff Distance between selections in A and B.
        Uses the external software tool Metro to do point-based mesh sampling
        """
        
        #We need meshes (polydata) for computing the Hausdorff distances
        meshA = None
        meshB = None
        #actually this should never happen, but let's keep it for making double sure
        if not self.surfaces.has_key(maskA.name):
            self._view_frame.dialog_exclaim('Mesh belonging to Mask A not found in list, and created on the fly. This is unexpected...', 'Unexpected program state')
            surface_creator_A = vtk.vtkDiscreteMarchingCubes()
            surface_creator_A.SetInput(maskA.data)
            surface_creator_A.Update()
            meshA = surface_creator_A.GetOutput()
        else:
            meshA = self.surfaces[maskA.name]

        #actually this should never happen, but let's keep it for making double sure
        if not self.surfaces.has_key(maskB.name):
            self._view_frame.dialog_exclaim('Mesh belonging to Mask B not found in list, and created on the fly. This is unexpected...', 'Unexpected program state')
            surface_creator_B = vtk.vtkDiscreteMarchingCubes()
            surface_creator_B.SetInput(maskB.data)
            surface_creator_B.Update()
            meshB = surface_creator_B.GetOutput()
        else:
            meshB = self.surfaces[maskB.name]

        filename_a = '@temp_mesh_a.ply'
        filename_b = '@temp_mesh_b.ply'

        ply_writer = vtk.vtkPLYWriter()
        ply_writer.SetFileTypeToBinary()
        print 'Writing temporary PLY mesh A = %s' % filename_a
        ply_writer.SetFileName(filename_a)
        ply_writer.SetInput(meshA)
        ply_writer.Update()
        print 'Writing temporary PLY mesh B = %s' % filename_b
        ply_writer.SetFileName(filename_b)
        ply_writer.SetInput(meshB)
        ply_writer.Update()

        command = 'metro.exe %s %s' % (filename_a, filename_b)
        p = subprocess.Popen(command, shell=True, stdout = subprocess.PIPE)
        outp = p.stdout.read()                          #The command line output from metro

        if len(outp) < 50:
            self._view_frame.dialog_error('Hausdorff distance computation requires Metro to be installed and available in the system path.\n\nMetro failed to execute.\n\nAborting.\n\nMetro may be downloaded from http://vcg.sourceforge.net/index.php/Metro', 'Metro was not found')
            return

        print 'Executing: %s' % command
        print '....................................'
        print outp
        print '....................................'

        index = outp.find('max')
        hdf = float(outp[index+6:index+54].split()[0])  #Forward Hausdorff distance
        index = outp.find('max', index+3)
        hdb = float(outp[index+6:index+54].split()[0])  #Backward Hausdorff distance

        index = outp.find('mean')
        mhdf = float(outp[index+7:index+35].split()[0])  #Forward Mean Hausdorff distance
        index = outp.find('mean', index+4)
        mhdb = float(outp[index+7:index+35].split()[0])  #Backward Mean Hausdorff distance

        hausdorff_distance = max(hdf, hdb)
        mean_hausdorff_distance = 0.5 * (mhdf + mhdb)

        print 'removing temporary files'
        os.remove(filename_a)
        os.remove(filename_b)
        print 'done!'

        print '\nSampled Hausdorff distance      = %.4f\nSampled Mean Hausdorff distance = %.4f\n' % (hausdorff_distance, mean_hausdorff_distance)

        return [hausdorff_distance, mean_hausdorff_distance]

    def _handler_compute_hausdorff_distance(self, event):
        """
        Computes the Hausdorff Distance between meshes in A and B.
        Uses the external software tool Metro to do point-based mesh sampling
        """
        if self.test_single_mask_pair_selection():
            names_a = self._view_frame.get_selected_mask_names_a()
            names_b = self._view_frame.get_selected_mask_names_b()
            maskA = self.masks[names_a.pop()]
            maskB = self.masks[names_b.pop()]

            [hausdorff_distance, _] = self._compute_hausdorff_distances(maskA, maskB)
            copy_to_clipboard = self._view_frame.dialog_yesno('Hausdorff distance = %.4f mm\n\nCopy to clipboard?' % hausdorff_distance, 'Hausdorff Distance')
            if copy_to_clipboard:
                self._view_frame.copy_text_to_clipboard('%f' % hausdorff_distance)

    def _handler_compute_mean_hausdorff_distance(self, event):
        """
        Computes the Mean Hausdorff Distance between meshes in A and B.
        Uses the external software tool Metro to do point-based mesh sampling
        """
        if self.test_single_mask_pair_selection():
            names_a = self._view_frame.get_selected_mask_names_a()
            names_b = self._view_frame.get_selected_mask_names_b()
            maskA = self.masks[names_a.pop()]
            maskB = self.masks[names_b.pop()]
            
            [_, mean_hausdorff_distance] = self._compute_hausdorff_distances(maskA, maskB)

            copy_to_clipboard = self._view_frame.dialog_yesno('Mean Hausdorff distance = %.4f mm\n\nCopy to clipboard?' % mean_hausdorff_distance, 'Mean Hausdorff distance')
            if copy_to_clipboard:
                self._view_frame.copy_text_to_clipboard('%f' % mean_hausdorff_distance)

    def _handler_mask_join(self, event):
        """Computes the union of the masks selected in boxes A and B.
        Saves the result as a new Mask
        """
        if self.test_valid_mask_selection_any():
            names_a = self._view_frame.get_selected_mask_names_a()
            names_b = self._view_frame.get_selected_mask_names_b()
            if len(names_a) + len(names_b) < 2:
                return
            union_masksA = self.compute_mask_union(names_a)
            union_masksB = self.compute_mask_union(names_b)
            new_mask = None
            if len(names_a) == 0:
                new_mask = union_masksB
            elif len(names_b) == 0:
                new_mask = union_masksA
            else:
                new_mask = self._logical_unite_masks(union_masksA, union_masksB)
            self.add_mask(new_mask)

    def _handler_mask_subtract(self, event):
        """Subtracts the the union of the masks selected in box B from the union of the masks selected in box A.
        Saves the result as a new Mask
        """
        if self.test_valid_mask_selection_a_and_b():
            names_a = self._view_frame.get_selected_mask_names_a()
            names_b = self._view_frame.get_selected_mask_names_b()
            union_masksA = self.compute_mask_union(names_a)
            union_masksB = self.compute_mask_union(names_b)
            new_mask = self._logical_subtract_masks(union_masksA, union_masksB)
            self.add_mask(new_mask)

    def _handler_mask_intersect(self, event):
        """Intersects the the union of the masks selected in box A with the union of the masks selected in box B.
        Saves the result as a new Mask
        """
        if self.test_valid_mask_selection_a_and_b():
            names_a = self._view_frame.get_selected_mask_names_a()
            names_b = self._view_frame.get_selected_mask_names_b()
            union_masksA = self.compute_mask_union(names_a)
            union_masksB = self.compute_mask_union(names_b)
            new_mask = self._logical_intersect_masks(union_masksA, union_masksB)
            self.add_mask(new_mask)

    def _test_intersections(self, mask_name_list):
        """
        Tests for intersections between the masks listed in mask_names
        """
        mask_names = copy.copy(mask_name_list)
        first_name = mask_names.pop()
        data = self.masks[first_name].data

        intersections_found = False
        eight_bit = False

        for mask_name in mask_names:
            print 'adding %s' % mask_name
            data2 = self.masks[mask_name].data
            adder = vtk.vtkImageMathematics()
            adder.SetOperationToAdd()
            adder.SetInput1(data)
            adder.SetInput2(data2)
            adder.Update()
            data = adder.GetOutput()

        accumulator = vtk.vtkImageAccumulate()
        accumulator.SetInput(data)
        accumulator.Update()
        max = accumulator.GetMax()[0]

        if max == 255:
            eight_bit = True
        elif max > 1:
            intersections_found = True
        else:
            self._view_frame.dialog_info("No intersections found.\n(duplicate selections in A and B ignored).", "No intersections")

        if eight_bit:
            eight_bit_mask_names = ''
            mask_names = copy.copy(mask_name_list)

            for mask_name in mask_names:
                accumulator = vtk.vtkImageAccumulate()
                accumulator.SetInput(self.masks[mask_name].data)
                accumulator.Update()
                if accumulator.GetMax()[0] == 255:
                    eight_bit_mask_names = '%s, "%s"' % (eight_bit_mask_names, mask_name)
            eight_bit_mask_names = eight_bit_mask_names[2:]     #Remove the first two characters for neat display purposes
            self._view_frame.dialog_error("Masks should be binary. The following masks were found to be 8-bit:\n%s" % eight_bit_mask_names,"Non-binary mask found!")

        elif intersections_found:
            mask_name_pair_list = ''
            mask_names = copy.copy(mask_name_list)

            while len(mask_names) > 0:
                name1 = mask_names.pop()

                for name2 in mask_names:
                    adder = vtk.vtkImageMathematics()
                    adder.SetOperationToAdd()
                    adder.SetInput1(self.masks[name1].data)
                    adder.SetInput2(self.masks[name2].data)
                    adder.Update()
                    accumulator = vtk.vtkImageAccumulate()
                    accumulator.SetInput(adder.GetOutput())
                    accumulator.Update()
                    if accumulator.GetMax()[0] == 2:
                        mask_name_pair_list = '%s,\n ("%s","%s")' % (mask_name_pair_list, name1, name2)
            mask_name_pair_list = mask_name_pair_list[2:]     #Remove the first two characters for neat display purposes
            self._view_frame.dialog_exclaim("Intersections found between the following mask pairs:\n%s" % mask_name_pair_list,"Intersections found!")

    def _test_dimensions(self, mask_names, msg):
        """
        Tests whether the given masks have matching volumetric dimensions.
        In practice mismatches can occur due to problems with feature generation algorithms (such as filtered backprojection)
        """
        masks_by_dimensions = {}
        masks_by_extent = {}
        masks_by_whole_extent = {}
        masks_by_spacing = {}

        for mask_name in mask_names:
            mask = self.masks[mask_name].data
            dimensions = mask.GetDimensions()
            spacing = mask.GetSpacing()
            extent = mask.GetExtent()
            whole_extent = mask.GetWholeExtent()

            if not masks_by_dimensions.has_key(dimensions):
                masks_by_dimensions[dimensions] = [str(mask_name)]
            else:
                masks_by_dimensions[dimensions].append(str(mask_name))

            if not masks_by_spacing.has_key(spacing):
                masks_by_spacing[spacing] = [str(mask_name)]
            else:
                masks_by_spacing[spacing].append(str(mask_name))

            if not masks_by_extent.has_key(extent):
                masks_by_extent[extent] = [str(mask_name)]
            else:
                masks_by_extent[extent].append(str(mask_name))

            if not masks_by_whole_extent.has_key(whole_extent):
                masks_by_whole_extent[whole_extent] = [str(mask_name)]
            else:
                masks_by_whole_extent[whole_extent].append(str(mask_name))


        if len(masks_by_dimensions.keys()) == 1 and len(masks_by_spacing.keys()) == 1 and len(masks_by_extent.keys()) == 1 and len(masks_by_whole_extent.keys()):
            dimension_report = '%s masks have the same dimensions, spacing, extent and whole extent:\n\n' % msg
            dimensions = masks_by_dimensions.keys().pop()
            dimension_report = '%s dimensions = %s\n' % (dimension_report, str(dimensions))
            dimensions = masks_by_spacing.keys().pop()
            dimension_report = '%s spacing = %s\n' % (dimension_report, str(dimensions))
            dimensions = masks_by_extent.keys().pop()
            dimension_report = '%s extent = %s\n' % (dimension_report, str(dimensions))
            dimensions = masks_by_whole_extent.keys().pop()
            dimension_report = '%s whole extent = %s\n' % (dimension_report, str(dimensions))
            
            self._view_frame.dialog_info(dimension_report, 'No mismatches')
        else:
            dimension_report = '% masks possess %d unique sets of dimensions. See below:\n' % (msg, len(masks_by_dimensions))
            for k in masks_by_dimensions.keys():
                dimension_report = '%s\n%s => %s' % (dimension_report, str(k), str( masks_by_dimensions[k]))
            dimension_report = '%s\n\n%d unique spacings with their defining masks:\n' % (dimension_report, len(masks_by_spacing))
            for k in masks_by_spacing.keys():
                dimension_report = '%s\n%s => %s' % (dimension_report, str(k), str( masks_by_spacing[k]))
            dimension_report = '%s\n\n%d unique extents with their defining masks:\n' % (dimension_report, len(masks_by_extent))
            for k in masks_by_extent.keys():
                dimension_report = '%s\n%s => %s' % (dimension_report, str(k), str( masks_by_extent[k]))
            dimension_report = '%s\n\n%d unique whole_extents with their defining masks:\n' % (dimension_report, len(masks_by_whole_extent))
            for k in masks_by_whole_extent.keys():
                dimension_report = '%s\n%s => %s' % (dimension_report, str(k), str( masks_by_whole_extent[k]))

            self._view_frame.dialog_exclaim(dimension_report,"Mismatches found!")

    def _handler_test_all_dimensions(self, event):
        """
        Tests whether any of the loaded masks have mismatching volume dimensions
        """
        if len(self.masks) < 2:
            self._view_frame.dialog_info("At least 2 masks need to be loaded to compare dimensions!","Fewer than two masks loaded")
            return

        mask_names = self.masks.keys()
        self._test_dimensions(mask_names, 'All')


    def _handler_test_selected_dimensions(self, event):
        """
        Tests the selected masks have mismatching volume dimensions
        """
        if self.test_valid_mask_selection_multiple():
            names_a = self._view_frame.get_selected_mask_names_a()
            names_b = self._view_frame.get_selected_mask_names_b()

            mask_names = names_a.copy()
            for name in names_b:
                mask_names.add(name)
            self._test_dimensions(mask_names, 'Selected')

    def _handler_test_all_intersections(self, event):
        """
        Tests whether there is an intersection between any of the loaded masks
        """
        if len(self.masks) < 2:
            self._view_frame.dialog_info("At least 2 masks need to be loaded to detect intersections!","Fewer than two masks loaded")
            return
                
        mask_names = self.masks.keys()
        self._test_intersections(mask_names)


    def _handler_test_selected_intersections(self, event):
        """
        Tests whether there is an intersection between the selected masks
        """
        if self.test_valid_mask_selection_multiple():
            names_a = self._view_frame.get_selected_mask_names_a()
            names_b = self._view_frame.get_selected_mask_names_b()
            mask_names = names_a.copy()
            for name in names_b:
                mask_names.add(name)
            self._test_intersections(mask_names)
            
    def compute_mask_union(self, mask_names_set):
        '''Computes and returns the union of a set of masks, identified by a set of mask names.'''
        mask_names = mask_names_set.copy()  #To prevent changes to the passed set due to popping
        united_mask = None

        if len(mask_names) > 0:
            mask_name = mask_names.pop()
            united_mask = self.masks[mask_name]
            for mask_name in mask_names:
                united_mask = self._logical_unite_masks(united_mask, self.masks[mask_name])
        return united_mask

    def test_single_mask_selection(self):
        selectionCountA = self._view_frame.list_ctrl_maskA.GetSelectedItemCount()
        selectionCountB = self._view_frame.list_ctrl_maskB.GetSelectedItemCount()

        if selectionCountA + selectionCountB > 1:
            self._view_frame.dialog_info("Multiple masks are selected in columns A and/or B.\nThis operation requires a single mask, either in A or B (but not both).","Multiple maks selected - invalid operation")
            return False
        return True

    def test_single_mask_pair_selection(self):
        selectionCountA = self._view_frame.list_ctrl_maskA.GetSelectedItemCount()
        selectionCountB = self._view_frame.list_ctrl_maskB.GetSelectedItemCount()

        if selectionCountA == 0:
            self._view_frame.dialog_info("No mask selected in column A.\nThis operation requires a single input each, for A and B.","Too few masks selected - invalid operation")
            return False
        if selectionCountB == 0:
            self._view_frame.dialog_info("No mask selected in column B.\nThis operation requires a single input each, for A and B.","Too few masks selected - invalid operation")
            return False
        if selectionCountA > 1:
            self._view_frame.dialog_info("Multiple masks are selected in column A.\nThis operation requires a single input each, for A and B.","Multiple maks selected - invalid operation")
            return False
        elif selectionCountB > 1:
            self._view_frame.dialog_info("Multiple masks are selected in column B.\nThis operation requires a single input each, for A and B.","Multiple maks selected - invalid operation")
            return False
        return True

    def test_valid_mask_selection_any(self, warn = True):
        selectionCountA = self._view_frame.list_ctrl_maskA.GetSelectedItemCount()
        selectionCountB = self._view_frame.list_ctrl_maskB.GetSelectedItemCount()

        if selectionCountA == 0 and selectionCountB == 0:
            if warn:
                self._view_frame.dialog_info("No masks are selected.","No masks selected")
            return False
        return True

    def test_valid_mask_selection_multiple(self, warn = True):
        names = self._view_frame.get_selected_mask_names_a()
        names_b = self._view_frame.get_selected_mask_names_b()
        for name in names_b:
            names.add(name)

        if len(names) < 2:
            if warn:
                self._view_frame.dialog_info("Fewer than two unique masks selected.","Too few masks selected")
            return False
        return True

    def test_valid_mask_selection_a_and_b(self, warn = True):
        selectionCountA = self._view_frame.list_ctrl_maskA.GetSelectedItemCount()
        selectionCountB = self._view_frame.list_ctrl_maskB.GetSelectedItemCount()

        if selectionCountA == 0:
            if warn:
                self._view_frame.dialog_info("No mask is selected in column A.\nThis operation requires inputs A and B.","Mask A not defined")
            return False
        elif selectionCountB == 0:
            if warn:
                self._view_frame.dialog_info("No mask is selected in column B.\nThis operation requires inputs A and B.","Mask B not defined")
            return False
        return True

    def test_valid_mask_selection_a_only(self, warn = True):
        selection_count_a = self._view_frame.list_ctrl_maskA.GetSelectedItemCount()

        if selection_count_a == 0:
            if warn:
                self._view_frame.dialog_info("This operation requires input from column A.","Mask A not defined")
            return False
        return True

    def test_valid_mask_selection_b_only(self, warn = True):
        selection_count_b = self._view_frame.list_ctrl_maskB.GetSelectedItemCount()

        if selection_count_b == 0:
            if warn:
                self._view_frame.dialog_info("This operation requires input from column B.","Mask B not defined")
            return False
        return True

    def _handler_close(self, event):
        "Closes this program"
        self.close()

    def _handler_introspect(self, event):
        self.miscObjectConfigure(self._view_frame, self, 'MaskComBinar')
        
    def render(self):
        """Method that calls Render() on the embedded RenderWindow.
        Use this after having made changes to the scene.
        """
        self._view_frame.render()

    def _logical_unite_masks(self, maskA, maskB):
        """Returns logical addition of maskA and maskB => maskA OR maskB"""        
        if maskA == None:
            return maskB
        elif maskB == None:
            return maskA
        print 'Joining masks %s and %s' % (maskA.name, maskB.name)
        logicOR = vtk.vtkImageLogic()
        logicOR.SetOperationToOr()
        logicOR.SetInput1(maskA.data)
        logicOR.SetInput2(maskB.data)
        logicOR.Update()

        result = self._threshold_image(logicOR.GetOutput(), 1, 255)
        return Mask('Merged','',result)

    def _logical_intersect_masks(self, maskA, maskB):        
        if maskA == None or maskB == None:
            return None
        print 'Intersecting masks %s and %s' % (maskA.name, maskB.name)
        logicAND = vtk.vtkImageLogic()
        logicAND.SetOperationToAnd()
        logicAND.SetInput1(maskA.data)
        logicAND.SetInput2(maskB.data)
        logicAND.Update()

        result = self._threshold_image(logicAND.GetOutput(), 1, 255)
        return Mask('Intersect','',result)

    def _logical_subtract_masks(self, maskA, maskB):
        """Returns logical subtraction of maskB from maskA => maskA AND (NOT maskB)"""        
        if maskB == None:
            return maskA
        print 'Subtracting mask %s and %s' % (maskA.name, maskB.name)
        logicNOT = vtk.vtkImageLogic()
        logicNOT.SetOperationToNot()
        logicNOT.SetInput1(maskB.data)
        logicNOT.Update()

        logicAND = vtk.vtkImageLogic()
        logicAND.SetOperationToAnd()
        logicAND.SetInput1(maskA.data)
        logicAND.SetInput2(logicNOT.GetOutput())
        logicAND.Update()

        result = self._threshold_image(logicAND.GetOutput(), 1, 255)
        return Mask('Diff','',result)

    def _threshold_image(self, image, lower, upper):
        """Thresholds a VTK Image, returning a signed short mask with 1 inside and 0 outside [lower, upper]"""
        thresholder = vtk.vtkImageThreshold()
        thresholder.SetInput(image)
        thresholder.ThresholdBetween(lower, upper)
        thresholder.SetInValue(1)
        thresholder.SetOutValue(0)
        thresholder.SetOutputScalarTypeToUnsignedChar()
        thresholder.Update()
        result = vtk.vtkImageData()
        result.DeepCopy(thresholder.GetOutput())
        return result

    def _split_disconnected_objects(self, source_mask):
        #This is done by labelling the objects from large to small
        #Convert to ITK
        thresholder = vtk.vtkImageThreshold()
        thresholder.SetInput(source_mask.data)
        thresholder.ThresholdBetween(1, 9999)
        thresholder.SetInValue(1)
        thresholder.SetOutValue(0)
        thresholder.SetOutputScalarTypeToShort()
        thresholder.Update()

        v2i = itk.VTKImageToImageFilter[itk.Image.SS3].New()
        v2i.SetInput(thresholder.GetOutput())

        ccf = itk.ConnectedComponentImageFilter.ISS3ISS3.New()
        ccf.SetInput(v2i.GetOutput())
        relabeller = itk.RelabelComponentImageFilter.ISS3ISS3.New()
        relabeller.SetInput(ccf.GetOutput())

        #convert back to VTK
        i2v = itk.ImageToVTKImageFilter[itk.Image.SS3].New()
        i2v.SetInput(relabeller.GetOutput())
        i2v.Update()
        labeled = i2v.GetOutput()

        accumulator = vtk.vtkImageAccumulate()
        accumulator.SetInput(labeled)
        accumulator.Update()
        nr_of_components = accumulator.GetMax()[0]
        print 'Found %d disconnected mask components' % nr_of_components

        message = '%d disconnected components found.\nHow many do you want to accept (large to small)?' % nr_of_components
        nr_to_process_str = self._view_frame.dialog_inputtext(message, 'Choose number of disconnected components', '1')[1]
        
        try:
            nr_to_process = int(nr_to_process_str)
        except:
            self._view_frame.dialog_error('Invalid numeric input: %s' % nr_to_process_str, "Invalid input")
            return

        if (nr_to_process < 0) or (nr_to_process > nr_of_components):
            self._view_frame.dialog_error('Number must be between 1 and %d' % nr_of_components, "Invalid input")
            return

        print 'Saving the largest %d components to new masks' % nr_to_process
        thresholder = vtk.vtkImageThreshold()
        thresholder.SetInput(labeled)
        thresholder.SetInValue(1)
        thresholder.SetOutValue(0)
        thresholder.SetOutputScalarTypeToUnsignedChar()        
        
        for i in range(1, nr_to_process+1):
            thresholder.ThresholdBetween(i, i)
            thresholder.Update()

            mask_data = vtk.vtkImageData()
            mask_data.DeepCopy(thresholder.GetOutput())

            new_mask = Mask('comp_%d' % i,'',mask_data)
            self.add_mask(new_mask)            