# Modified by Francois Malan, LUMC / TU Delft
# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor
import wx
import wx.lib.inspection
import vtk

# wxPython 2.8.8.1 wx.aui bugs severely on GTK. See:
# http://trac.wxwidgets.org/ticket/9716
# Until this is fixed, use this PyAUI to which I've added a
# wx.aui compatibility layer.
if wx.Platform == "__WXGTK__":
    from external import PyAUI
    wx.aui = PyAUI
else:
    import wx.aui

import MaskComBinarPanels
reload(MaskComBinarPanels)

class MaskComBinarFrame(wx.Frame):
    """wx.Frame child class used by MaskComBinar for its
    interface.

    This is an AUI-managed window, so we create the top-level frame,
    and then populate it with AUI panes.
    """

    def __init__(self, parent, id=-1, title="", name=""):
        wx.Frame.__init__(self, parent, id=id, title=title, 
                pos=wx.DefaultPosition, size=(800,600), name=name)

        self._create_menubar()

        # tell FrameManager to manage this frame        
        self._mgr = wx.aui.AuiManager()
        self._mgr.SetManagedWindow(self)

        self._mgr.AddPane(self._create_mask_operations_pane(), wx.aui.AuiPaneInfo().
                          Name("operations").Caption("Operations").Left().

                          BestSize(wx.Size(275, 65)).
                          CloseButton(False).MaximizeButton(True))

        self._mgr.AddPane(self._create_mask_lists_pane(), wx.aui.AuiPaneInfo().
                          Name("masks").Caption("Masks").Left().

                          BestSize(wx.Size(275, 450)).
                          CloseButton(False).MaximizeButton(True))


        self._mgr.AddPane(self._create_rwi2d_pane(), wx.aui.AuiPaneInfo().
                          Name("rwi2D").Caption("2D").
                          Right().
                          BestSize(wx.Size(300,500)).
                          CloseButton(False).MaximizeButton(True))

        self._mgr.AddPane(self._create_rwi3d_pane(), wx.aui.AuiPaneInfo().
                          Name("rwi3D").Caption("3D").
                          Center().
                          BestSize(wx.Size(300,500)).
                          CloseButton(False).MaximizeButton(True))

        self.SetMinSize(wx.Size(400, 300))

        # first we save this default perspective with all panes
        # visible
        self._perspectives = {} 
        self._perspectives['default'] = self._mgr.SavePerspective()

        # then we hide all of the panes except the renderer
        #self._mgr.GetPane("Masks").Hide()
        self._mgr.GetPane("files").Hide()
        self._mgr.GetPane("meta").Hide()
        # save the perspective again
        self._perspectives['max_image'] = self._mgr.SavePerspective()

        # and put back the default perspective / view
        self._mgr.LoadPerspective(self._perspectives['default'])

        # finally tell the AUI manager to do everything that we've
        # asked
        self._mgr.Update()

#        # we bind the views events here, because the functionality is
#        # completely encapsulated in the frame and does not need to
#        # round-trip to the DICOMBrowser main module.
#        self.Bind(wx.EVT_MENU, self._handler_default_view,
#                id=views_default_id)
#
#        self.Bind(wx.EVT_MENU, self._handler_max_image_view,
#                id=views_max_image_id)

    def close(self):
       self.Destroy()

    def _create_menubar(self):
        self.menubar = wx.MenuBar()
        self.SetMenuBar(self.menubar)

        menu_file = wx.Menu()
        self.id_open_binary_mask = wx.NewId()
        menu_file.Append(self.id_open_binary_mask, "&Open binary Mask\tCtrl-O",
                "Open a binary mask", wx.ITEM_NORMAL)

        self.id_open_multi_mask = wx.NewId()
        menu_file.Append(self.id_open_multi_mask, "&Open multilabel Mask\tCtrl-Alt-O",
                "Open an integer-labeled mask", wx.ITEM_NORMAL)

        self.id_open_mask_dir = wx.NewId()
        menu_file.Append(self.id_open_mask_dir, "&Open Directory\tCtrl-Shift-O",
                "Open all masks from a directory", wx.ITEM_NORMAL)

        self.id_save_mask = wx.NewId()
        menu_file.Append(self.id_save_mask, "&Save Mask\tCtrl-S",
                "Save a mask", wx.ITEM_NORMAL)

        self.id_quit = wx.NewId()
        menu_file.Append(self.id_quit, "&Exit\tCtrl-Q",
                "Exit MaskCo", wx.ITEM_NORMAL)

        menu_advanced = wx.Menu()
        self.id_introspect = wx.NewId()
        menu_advanced.Append(self.id_introspect, "Introspect",
                "Exit MaskCo", wx.ITEM_NORMAL)
                
        self.menubar.Append(menu_file, "&File")
        self.menubar.Append(menu_advanced, "&Advanced")

    def _create_rwi2d_pane(self):
        panel = wx.Panel(self, -1)
        
        self.rwi2d = wxVTKRenderWindowInteractor(panel, -1, (400,400))                
        self.reset_cam2d_button = wx.Button(panel, -1, "Reset View")
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(self.reset_cam2d_button)

        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer1.Add(self.rwi2d, 1, wx.EXPAND|wx.BOTTOM, 7)
        sizer1.Add(button_sizer)
        
        tl_sizer = wx.BoxSizer(wx.VERTICAL)
        tl_sizer.Add(sizer1, 1, wx.ALL|wx.EXPAND, 7)

        panel.SetSizer(tl_sizer)
        tl_sizer.Fit(panel)

        return panel

    def _create_rwi3d_pane(self):
        panel = wx.Panel(self, -1)

        self.rwi3d = wxVTKRenderWindowInteractor(panel, -1, (400,400))
        istyle = vtk.vtkInteractorStyleTrackballCamera()
        self.rwi3d.SetInteractorStyle(istyle)

        self.reset_cam3d_button = wx.Button(panel, -1, "Reset Zoom")
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(self.reset_cam3d_button)

        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer1.Add(self.rwi3d, 1, wx.EXPAND|wx.BOTTOM, 7)
        sizer1.Add(button_sizer)

        tl_sizer = wx.BoxSizer(wx.VERTICAL)
        tl_sizer.Add(sizer1, 1, wx.ALL|wx.EXPAND, 7)

        panel.SetSizer(tl_sizer)
        tl_sizer.Fit(panel)
        return panel

    def _create_mask_lists_pane(self):
        # instantiated wxGlade frame
        iff = MaskComBinarPanels.MaskListsFrame(self, id=-1,size=(600,200))
        panel = iff.mask_lists_panel
        # reparent the panel to us
        panel.Reparent(self)

        self.list_ctrl_maskA = iff.list_ctrl_maskA
        self.list_ctrl_maskB = iff.list_ctrl_maskB
        self.clear_selection_button = iff.button_clear_selection
        self.masks_pane = panel

        iff.Destroy()
        return panel

    def _create_mask_operations_pane(self):
        # instantiated wxGlade frame
        iff = MaskComBinarPanels.MaskOperationsFrame(self, id=-1,size=(600,200))
        panel = iff.mask_operations_panel
        # reparent the panel to us
        panel.Reparent(self)

        self.mask_join_button = iff.add_button
        self.mask_subtract_button = iff.subtract_button
        self.mask_intersect_button = iff.and_button

        self.mask_align_metadata_button = iff.align_metadata_button
        self.mask_align_icp_button = iff.align_icp_button
        self.split_disconnected_button = iff.split_disconnected_button

        self.test_selected_dimensions_button = iff.check_selected_dimensions_button
        self.test_all_dimensions_button = iff.check_all_dimensions_button
        self.test_selected_intersections_button = iff.check_selected_overlaps_button
        self.test_all_intersections_button = iff.check_all_overlaps_button
        self.operations_pane = panel

        self.volume_button = iff.volume_button
        self.dice_coefficient_button = iff.dice_button
        self.hausdorff_distance_button = iff.hausdorff_button
        self.mean_hausdorff_distance_button = iff.mean_hausdorff_button

        iff.Destroy()
        return panel

    def render(self):
        """Update embedded RWI, i.e. update the image.
        """
        self.rwi2d.Render()
        self.rwi3d.Render()
       
    def _handler_default_view(self, event):
        """Event handler for when the user selects View | Default from
        the main menu.
        """
        self._mgr.LoadPerspective(
                self._perspectives['default'])

    def _handler_max_image_view(self, event):
        """Event handler for when the user selects View | Max Image
        from the main menu.
        """
        self._mgr.LoadPerspective(
            self._perspectives['max_image'])

    def clear_selections(self):
        indices = self._get_selected_indices_in_listctrl(self.list_ctrl_maskA)
        for i in indices:
            self.list_ctrl_maskA.Select(i, 0)
        indices = self._get_selected_indices_in_listctrl(self.list_ctrl_maskB)
        for i in indices:
            self.list_ctrl_maskB.Select(i, 0)

    def _get_selected_indices_in_listctrl(self, listctrl):
        '''Returns the indices of items selected in the provided listctrl'''
        indices = set()
        index = -1
        while True:
            index = listctrl.GetNextItem(index, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
            if index == -1:
                break
            else:
                indices.add(index)
        return indices

    def _get_all_indices_in_listctrl(self, listctrl):
        '''Returns the indices of items selected in the provided listctrl'''
        indices = set()
        index = -1
        while True:
            index = listctrl.GetNextItem(index, wx.LIST_NEXT_ALL)
            if index == -1:
                break
            else:
                indices.add(index)
        return indices

    def _get_selected_mask_names_in_listctrl(self, listctrl):
        '''Returns the unique identifying names of masks selected in the provided listctrl'''
        indices = self._get_selected_indices_in_listctrl(listctrl)
        mask_names = set()
        for i in indices:
            mask_names.add(listctrl.GetItem(i).GetText())
        return mask_names

    def get_selected_mask_names_a(self):
        '''Returns the unique identifying names of masks selected in mask list A'''
        return self._get_selected_mask_names_in_listctrl(self.list_ctrl_maskA)

    def get_selected_mask_names_b(self):
        '''Returns the unique identifying names of masks selected in mask list B'''
        return self._get_selected_mask_names_in_listctrl(self.list_ctrl_maskB)

    def add_mask(self, mask_name):
        num_items = self.list_ctrl_maskA.GetItemCount() #Should be identical for list B
        num_itemsB = self.list_ctrl_maskB.GetItemCount()
        if num_items != num_itemsB:
            self.dialog_error("Numer of items in Lists A doesn't match list B! (%d vs %d)" % (num_items, num_itemsB), "Mask list mismatch!")

        self.list_ctrl_maskA.InsertStringItem(num_items, mask_name)
        self.list_ctrl_maskB.InsertStringItem(num_items, mask_name)

    def delete_mask(self, mask_name):
        indices = self._get_all_indices_in_listctrl(self.list_ctrl_maskA)
        for index in indices:
            list_name = self.list_ctrl_maskA.GetItem(index).GetText()
            if list_name == mask_name:
                self.list_ctrl_maskA.DeleteItem(index)
                self.list_ctrl_maskB.DeleteItem(index)
                break
        return

    def dialog_info(self, message, title):
        dlg = wx.MessageDialog(self, message,title,wx.OK)
        dlg.ShowModal()

    def dialog_exclaim(self, message, title):
        dlg = wx.MessageDialog(self, message,title,wx.OK|wx.ICON_EXCLAMATION)
        dlg.ShowModal()

    def dialog_error(self, message, title):
        dlg = wx.MessageDialog(self, message,title,wx.OK|wx.ICON_ERROR)
        dlg.ShowModal()

    def dialog_yesno(self, message, title):
        dlg = wx.MessageDialog(self, message,title,wx.YES_NO|wx.NO_DEFAULT)
        return (dlg.ShowModal() == wx.ID_YES)

    def dialog_inputtext(self, message, title, default_text):
        dlg = wx.TextEntryDialog(self, message, title, default_text)
        return [(dlg.ShowModal() == wx.ID_OK), dlg.GetValue()]

    def copy_text_to_clipboard(self, text_message):
       clipdata = wx.TextDataObject()
       clipdata.SetText(text_message)
       wx.TheClipboard.Open()
       wx.TheClipboard.SetData(clipdata)
       wx.TheClipboard.Close()
       print 'Text copied to clipboard: %s' % text_message
