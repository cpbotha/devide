# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

# Hello there person reading this source!
# At the moment, I'm trying to get a fully-functioning DICOM browser
# out the door as fast as possible.  As soon as the first version is
# out there and my one user can start giving feedback, the following
# major changes are planned:
# * refactoring of the code, specifically to get the dicom slice
#   viewer out into a separate class for re-use in the rest of DeVIDE,
#   for example by the light-table thingy I'm planning.  See issue 38.
# * caching of DICOM searches: a scan of a set of directories will
#   create an sqlite file with all scanned information.  Name of sql
#   file will be stored in config, so that restarts will be REALLY
#   quick.  One will be able to scan (recreate whole cache file) or
#   a quick re-scan (only add new files that have appeared, remove 
#   files that have disappeared).  See issue 39.

# - drag-drop support (dragging from series, or selection of files in
#   file listbox)
# - create menu bar with:
#   * reset default view (aui perspective)
#   * changing focus to various bits, with hot keys; e.g. ctrl-f goes
#     to image file listing.

# for the drag-drop support:
# you need to create a wx.FileDataObject that can be dragged and
# dropped on e.g. the DICOMReader module

import DICOMBrowserFrame
reload(DICOMBrowserFrame)
import gdcm
from module_kits.misc_kit import misc_utils
from moduleBase import moduleBase
from moduleMixins import introspectModuleMixin
import moduleUtils
import os
import sys
import traceback
import vtk
import vtkgdcm
import wx

class Study:
    def __init__(self):
        self.patient_name = None
        self.patient_id = None
        self.uid = None
        self.description = None
        self.date = None
        # maps from series_uid to Series instance
        self.series_dict = {}
        # total number of slices in complete study
        self.slices = 0

class Series:
    def __init__(self):
        self.uid = None
        self.description = None
        self.modality = None
        self.filenames = []
        # number of slices can deviate from number of filenames due to
        # multi-frame DICOM files
        self.slices = 0
        self.rows = 0
        self.columns = 0

class DICOMBrowser(introspectModuleMixin, moduleBase):
    def __init__(self, module_manager):
        moduleBase.__init__(self, module_manager)

        introspectModuleMixin.__init__(
            self,
            {'Module (self)' : self})

        self._view_frame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager, 
            DICOMBrowserFrame.DICOMBrowserFrame)
        # change the title to something more spectacular
        # default is DICOMBrowser View
        self._view_frame.SetTitle('DeVIDE DICOMBrowser')

        self._image_viewer = None
        self._setup_image_viewer()

        # map from study_uid to Study instances
        self._study_dict = {}
        # map from studies listctrl itemdata to study uid
        self._item_data_to_study_uid = {}
        # currently selected study_uid
        self._selected_study_uid = None

        self._item_data_to_series_uid = {}
        self._selected_series_uid = None

        self._bind_events()


        self._config.dicom_search_paths = []
        self._config.lock_pz = False
        self._config.lock_wl = False

        self.sync_module_logic_with_config()
        self.sync_module_view_with_logic()

        self.view()
        # all modules should toggle this once they have shown their
        # stuff.
        self.view_initialised = True

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
        del self._image_viewer
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
        # show DICOM search paths in interface
        tc = self._view_frame.dirs_pane.dirs_files_tc
        tc.SetValue(self._helper_dicom_search_paths_to_string(
            self._config.dicom_search_paths))

        # show value of pz and wl locks
        ip = self._view_frame.image_pane
        ip.lock_pz_cb.SetValue(self._config.lock_pz)
        ip.lock_wl_cb.SetValue(self._config.lock_wl)

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
        self._view_frame.render_image()

    def _bind_events(self):
        fp = self._view_frame.dirs_pane

        fp.ad_button.Bind(wx.EVT_BUTTON,
                self._handler_ad_button)

        fp.af_button.Bind(wx.EVT_BUTTON,
                self._handler_af_button)

        fp.scan_button.Bind(wx.EVT_BUTTON,
                self._handler_scan_button)
        
        lc = self._view_frame.studies_lc
        lc.Bind(wx.EVT_LIST_ITEM_SELECTED,
                self._handler_study_selected)

        lc = self._view_frame.series_lc
        lc.Bind(wx.EVT_LIST_ITEM_SELECTED,
                self._handler_series_selected)
        # with this one, we'll catch drag events
        lc.Bind(wx.EVT_MOTION, self._handler_series_motion)

        lc = self._view_frame.files_lc
        # we use this event instead of focused, as group / multi
        # selections (click, then shift click 5 items down) would fire
        # selected events for ALL involved items.  With FOCUSED, only
        # the item actually clicked on, or keyboarded to, gets the
        # event.
        lc.Bind(wx.EVT_LIST_ITEM_FOCUSED,
                self._handler_file_selected)
    
        # catch drag events (so user can drag and drop selected files)
        lc.Bind(wx.EVT_MOTION, self._handler_files_motion)

        # keep track of the image viewer controls
        ip = self._view_frame.image_pane
        ip.lock_pz_cb.Bind(wx.EVT_CHECKBOX,
                self._handler_lock_pz_cb)
        ip.lock_wl_cb.Bind(wx.EVT_CHECKBOX,
                self._handler_lock_wl_cb)
        ip.reset_b.Bind(wx.EVT_BUTTON,
                self._handler_image_reset_b)

    def _fill_files_listctrl(self):
        # get out current Study instance
        study = self._study_dict[self._selected_study_uid]
        # then the series_dict belonging to that Study
        series_dict = study.series_dict
        # and finally the specific series instance
        series = series_dict[self._selected_series_uid]

        lc = self._view_frame.files_lc
        lc.DeleteAllItems()

        self._item_data_to_file = {}

        for filename in series.filenames:
            idx = lc.InsertStringItem(sys.maxint, filename)
            lc.SetItemData(idx, idx)
            self._item_data_to_file[idx] = filename
        
        # make sure the column shows the full length of the fn
        # why does this sometimes not capture the full length?
        lc.auto_size_columns()

        # select the first file
        if lc.GetItemCount() > 0:
            lc.SetItemState(0, wx.LIST_STATE_SELECTED,
                    wx.LIST_STATE_SELECTED)
            # in this case we have to focus as well, as that's the
            # event that it's sensitive to.
            lc.SetItemState(0, wx.LIST_STATE_FOCUSED,
                    wx.LIST_STATE_FOCUSED)


    def _fill_series_listctrl(self):
        # get out current Study instance
        study = self._study_dict[self._selected_study_uid]
        # then the series_dict belonging to that Study
        series_dict = study.series_dict

        # clear the ListCtrl
        lc = self._view_frame.series_lc
        lc.DeleteAllItems()
        # shortcut to the columns class
        sc = DICOMBrowserFrame.SeriesColumns

        # we're going to need this for the column sorting
        item_data_map = {}
        self._item_data_to_series_uid = {}

        for series_uid, series in series_dict.items():
            idx = lc.InsertStringItem(sys.maxint, series.description)
            lc.SetStringItem(idx, sc.modality, series.modality)
            lc.SetStringItem(idx, sc.num_images, str(series.slices))
            rc_string = '%d x %d' % (series.columns, series.rows)
            lc.SetStringItem(idx, sc.row_col, rc_string)
            
            # also for the column sorting
            lc.SetItemData(idx, idx)

            item_data_map[idx] = (
                series.description,
                series.modality,
                series.slices,
                rc_string)

            self._item_data_to_series_uid[idx] = series.uid

        lc.itemDataMap = item_data_map

        # select the first series
        if lc.GetItemCount() > 0:
            lc.SetItemState(0, wx.LIST_STATE_SELECTED,
                    wx.LIST_STATE_SELECTED)

    def _fill_studies_listctrl(self):
        """Given a study dictionary, fill out the complete studies
        ListCtrl.
        """

        lc = self._view_frame.studies_lc
        # clear the thing out
        lc.DeleteAllItems()

        sc = DICOMBrowserFrame.StudyColumns

        # this is for the columnsorter
        item_data_map = {}
        # this is for figuring out which study is selected in the
        # event handler
        self.item_data_to_study_id = {}
        for study_uid, study in self._study_dict.items():
            # clean way of mapping from item to column?
            idx = lc.InsertStringItem(sys.maxint, study.patient_name)
            lc.SetStringItem(idx, sc.patient_id, study.patient_id)
            lc.SetStringItem(idx, sc.description, study.description)
            lc.SetStringItem(idx, sc.date, study.date)
            lc.SetStringItem(idx, sc.num_images, str(study.slices))
            lc.SetStringItem(
                    idx, sc.num_series, str(len(study.series_dict)))
          
            # we set the itemdata to the current index (this will
            # change with sorting, of course)
            lc.SetItemData(idx, idx) 

            # for sorting we build up this item_data_map with the same
            # hash as key, and the all values occurring in the columns
            # as sortable values
            item_data_map[idx] = (
                    study.patient_name,
                    study.patient_id,
                    study.description,
                    study.date,
                    study.slices,
                    len(study.series_dict))

            self._item_data_to_study_uid[idx] = study.uid

        # assign the datamap to the ColumnSorterMixin
        lc.itemDataMap = item_data_map
        
        if lc.GetItemCount() > 0:
            lc.SetItemState(0, wx.LIST_STATE_SELECTED,
                    wx.LIST_STATE_SELECTED)

        #lc.auto_size_columns()

    def _handler_ad_button(self, event):

        dlg = wx.DirDialog(self._view_frame, 
            "Choose a directory to add:",
                          style=wx.DD_DEFAULT_STYLE
                           | wx.DD_DIR_MUST_EXIST
                           )

        if dlg.ShowModal() == wx.ID_OK:
            p = dlg.GetPath()
            tc = self._view_frame.dirs_pane.dirs_files_tc
            v = tc.GetValue()
            nv = self._helper_dicom_search_paths_to_string(
                    [v, p])
            tc.SetValue(nv)

        dlg.Destroy()

    def _handler_af_button(self, event):

        dlg = wx.FileDialog(
                self._view_frame, message="Choose files to add:",
                defaultDir="", 
                defaultFile="",
                wildcard="All files (*.*)|*.*",
                style=wx.OPEN | wx.MULTIPLE
                )

        if dlg.ShowModal() == wx.ID_OK:
            tc = self._view_frame.dirs_pane.dirs_files_tc
            v = tc.GetValue()
            nv = self._helper_dicom_search_paths_to_string(
                    [v] + dlg.GetPaths())


        dlg.Destroy()

    def _handler_file_selected(self, event):
        lc = self._view_frame.files_lc
        idx = lc.GetItemData(event.m_itemIndex)
        filename = self._item_data_to_file[idx]

        r = vtkgdcm.vtkGDCMImageReader()
        r.SetFileName(filename)

        try:
            r.Update()
        except RuntimeWarning, e:
            # reader generates warning of overlay information can't be
            # read.  We should change the VTK exception support to
            # just output some text with a warning and not raise an
            # exception.
            traceback.print_exc()
            # with trackback.format_exc() you can send this to the log
            # window.

        self._update_image(r)
        self._update_meta_data_pane(r)

    def _update_image(self, gdcm_reader):
        """Given a vtkGDCMImageReader instance that has read the given
        file, update the image viewer.
        """

        r = gdcm_reader

        self._image_viewer.SetInput(r.GetOutput())
        #if r.GetNumberOfOverlays():
        #    self._image_viewer.AddInput(r.GetOverlay(0))

        # now make the nice text overlay thingies!

        # DirectionCosines: first two columns are X and Y in the RAH
        # space
        dc = r.GetDirectionCosines()

        x_cosine = \
                dc.GetElement(0,0), dc.GetElement(1,0), dc.GetElement(2,0)

        rah = misc_utils.major_axis_from_iop_cosine(x_cosine)
        if rah:
            self._image_viewer.xl_text_actor.SetInput(rah[0])
            self._image_viewer.xr_text_actor.SetInput(rah[1])
        else:
            self._image_viewer.xl_text_actor.SetInput('X')
            self._image_viewer.xr_text_actor.SetInput('X')

        y_cosine = \
                dc.GetElement(0,1), dc.GetElement(1,1), dc.GetElement(2,1)
        rah = misc_utils.major_axis_from_iop_cosine(y_cosine)

        if rah:
            # we have to swap these around because VTK has the
            # convention of image origin at the upper left and GDCM
            # dutifully swaps the images when loading to follow this
            # convention.  Direction cosines (IOP) is not swapped, so
            # we have to compensate here.
            self._image_viewer.yb_text_actor.SetInput(rah[1])
            self._image_viewer.yt_text_actor.SetInput(rah[0])
        else:
            self._image_viewer.yb_text_actor.SetInput('X')
            self._image_viewer.yt_text_actor.SetInput('X')

        d = r.GetOutput().GetDimensions()
        ul = self._image_viewer.ul_text_actor
        ul.SetInput('Image Size: %d x %d' % (d[0], d[1]))

        ur = self._image_viewer.ur_text_actor
        mip = r.GetMedicalImageProperties()
        ur.SetInput('%s\n%s\n%s\n%s' % (
            mip.GetPatientName(),
            mip.GetPatientID(),
            mip.GetStudyDescription(),
            mip.GetSeriesDescription()))

        br = self._image_viewer.br_text_actor
        br.SetInput('DeVIDE\nTU Delft')

        # we have a new image in the image_viewer, so we have to reset
        # the camera so that the image is visible.
        if not self._config.lock_pz:
            self._reset_image_pz()

        # also reset window level
        if not self._config.lock_wl:
            self._reset_image_wl()

        self._image_viewer.Render()



    def _update_meta_data_pane(self, gdcm_reader):
        """Given a vtkGDCMImageReader instance that was used to read a
        file, update the meta-data display.
        """

        # update image meta-data #####
        r = gdcm_reader
        mip = r.GetMedicalImageProperties()

        r_attr_l = [
                'DataOrigin',
                'DataSpacing'
        ]

        import module_kits.vtk_kit
        mip_attr_l = \
            module_kits.vtk_kit.constants.medical_image_properties_keywords
                


        item_data_map = {}
        lc = self._view_frame.meta_lc

        # only start over if we have to to avoid flickering and
        # resetting of scroll bars.
        if lc.GetItemCount() != (len(r_attr_l) + len(mip_attr_l)):
            lc.DeleteAllItems() 
            reset_lc = True
        else:
            reset_lc = False

        def helper_av_in_lc(a, v, idx):
            if reset_lc:
                # in the case of a reset (i.e. we have to build up the
                # listctrl from scratch), the idx param is ignored as
                # we overwrite it with our own here
                idx = lc.InsertStringItem(sys.maxint, a)
            else:
                # not a reset, so we use the given idx
                lc.SetStringItem(idx, 0, a)

            lc.SetStringItem(idx, 1, v)
            lc.SetItemData(idx, idx)
            item_data_map[idx] = (a, v)

        idx = 0
        for a in r_attr_l:
            v = str(getattr(r, 'Get%s' % (a,))())
            helper_av_in_lc(a, v, idx)
            idx = idx + 1

        for a in mip_attr_l:
            v = str(getattr(mip, 'Get%s' % (a,))())
            helper_av_in_lc(a, v, idx)
            idx = idx + 1

        # so that sorting (kinda) works
        lc.itemDataMap = item_data_map

    def _handler_image_reset_b(self, event):
        self._reset_image_pz()
        self._reset_image_wl()
        self._image_viewer.Render()
        
    def _handler_lock_pz_cb(self, event):
        cb = self._view_frame.image_pane.lock_pz_cb 
        self._config.lock_pz = cb.GetValue()

        # when the user unlocks pan/zoom, reset it for the current
        # image
        if not self._config.lock_pz:
            self._reset_image_pz()
            self._image_viewer.Render()
      

    def _handler_lock_wl_cb(self, event):
        cb = self._view_frame.image_pane.lock_wl_cb 
        self._config.lock_wl = cb.GetValue()
        
        # when the user unlocks window / level, reset it for the
        # current image
        if not self._config.lock_wl:
            self._reset_image_wl()
            self._image_viewer.Render()

    def _handler_scan_button(self, event):
        tc = self._view_frame.dirs_pane.dirs_files_tc

        # helper function discards empty strings and strips the rest
        paths = self._config.dicom_search_paths = \
                self._helper_dicom_search_paths_to_list(tc.GetValue())

        # let's put it back in the interface too
        tc.SetValue(self._helper_dicom_search_paths_to_string(paths))

        self._study_dict = self._scan(paths)
        self._fill_studies_listctrl()

    def _handler_files_motion(self, event):
        """Handler for when user drags a file selection somewhere.
        """

        if not event.Dragging():
            event.Skip()
            return

        lc = self._view_frame.files_lc

        selected_idxs = []
        s = lc.GetFirstSelected()
        while s != -1:
            selected_idxs.append(s)
            s = lc.GetNextSelected(s)

        if len(selected_idxs) > 0:
            data_object = wx.FileDataObject()
            for idx in selected_idxs:
                data_object.AddFile(self._item_data_to_file[idx])

            drop_source = wx.DropSource(lc)
            drop_source.SetData(data_object)
            drop_source.DoDragDrop(False)

    def _handler_series_motion(self, event):
        if not event.Dragging():
            event.Skip()
            return

        # get out current Study instance
        try:
            study = self._study_dict[self._selected_study_uid]
        except KeyError:
            return

        # then the series_dict belonging to that Study
        series_dict = study.series_dict
        # and finally the specific series instance
        # series.filenames is a list of the filenames
        try:
            series = series_dict[self._selected_series_uid]
        except KeyError:
            return

        # according to the documentation, we can only write to this
        # object on Windows and GTK2.  Hrrmmpph.
        # FIXME.  Will have to think up an alternative solution on
        # OS-X
        data_object = wx.FileDataObject()
        for f in series.filenames:
            data_object.AddFile(f)

        drop_source = wx.DropSource(self._view_frame.series_lc)
        drop_source.SetData(data_object)
        # False means that files will be copied, NOT moved
        drop_source.DoDragDrop(False)

    def _handler_series_selected(self, event):
        lc = self._view_frame.series_lc
        idx = lc.GetItemData(event.m_itemIndex)
        series_uid = self._item_data_to_series_uid[idx]
        self._selected_series_uid = series_uid

        print 'series_uid', series_uid

        self._fill_files_listctrl()

    def _handler_study_selected(self, event):
        # we get the ItemData from the currently selected ListCtrl
        # item
        lc = self._view_frame.studies_lc
        idx = lc.GetItemData(event.m_itemIndex)
        # and then use this to find the current study_uid
        study_uid = self._item_data_to_study_uid[idx]
        self._selected_study_uid = study_uid

        print 'study uid', study_uid

        self._fill_series_listctrl()

    def _helper_dicom_search_paths_to_string(
            self, dicom_search_paths):
        """Given a list of search paths, append them into a semicolon
        delimited string.
        """
        s = [i.strip() for i in dicom_search_paths]
        s2 = [i for i in s if len(i) > 0]
        return ' ; '.join(s2)

    def _helper_dicom_search_paths_to_list(
            self, dicom_search_paths):
        """Given a semicolon-delimited string, break into list.
        """

        s = [i.strip() for i in dicom_search_paths.split(';')]
        return [i for i in s if len(i) > 0]

    def _helper_recursive_glob(self, paths):
        """Given a combined list of files and directories, return a
        combined list of sorted and unique fully-qualified filenames,
        consisting of the supplied filenames and a recursive search
        through all supplied directories.
        """

        # we'll use this to keep all filenames unique 
        files_dict = {}
        d = gdcm.Directory()

        for path in paths:
            if os.path.isdir(path):
                # we have to cast path to str (it's usually unicode)
                # else the gdcm wrappers error on "bad number of
                # arguments to overloaded function"
                d.Load(str(path), True)
                # fromkeys creates a new dictionary with GetFilenames
                # as keys; then update merges this dictionary with the
                # existing files_dict
                normed = [os.path.normpath(i) for i in d.GetFilenames()]
                files_dict.update(dict.fromkeys(normed, 1))

            elif os.path.isfile(path):
                files_dict[os.path.normpath(path)] = 1


        # now sort everything
        filenames = files_dict.keys()
        filenames.sort()

        return filenames

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

    def _scan(self, paths):
        """Given a list combining filenames and directories, search
        recursively to find all valid DICOM files.  Build
        dictionaries.
        """

        # UIDs are unique for their domains.  Patient ID for example
        # is not unique.
        # Instance UID (0008,0018)
        # Patient ID (0010,0020)
        # Study UID (0020,000D) - data with common procedural context
        # Study description (0008,1030)
        # Series UID (0020,000E)

        # see http://public.kitware.com/pipermail/igstk-developers/
        # 2006-March/000901.html for explanation w.r.t. number of
        # frames; for now we are going to assume that this refers to
        # the number of included slices (as is the case for the
        # Toshiba 320 slice for example)

        tag_to_symbol = {
                (0x0008, 0x0018) : 'instance_uid',
                (0x0010, 0x0010) : 'patient_name',
                (0x0010, 0x0020) : 'patient_id',
                (0x0020, 0x000d) : 'study_uid',
                (0x0008, 0x1030) : 'study_description',
                (0x0008, 0x0020) : 'study_date',
                (0x0020, 0x000e) : 'series_uid',
                (0x0008, 0x103e) : 'series_description',
                (0x0008, 0x0060) : 'modality', # fixed per series
                (0x0028, 0x0008) : 'number_of_frames',
                (0x0028, 0x0010) : 'rows',
                (0x0028, 0x0011) : 'columns'
                }

        # find list of unique and sorted filenames
        filenames = self._helper_recursive_glob(paths)

        s = gdcm.Scanner()
        # add the tags we want to the scanner
        for tag_tuple in tag_to_symbol:
            tag = gdcm.Tag(*tag_tuple)
            s.AddTag(tag)

        # d.GetFilenames simply returns a tuple with all
        # fully-qualified filenames that it finds.
        ret = s.Scan(filenames)
        if not ret:
            print "scanner failed"
            return

        # s now contains a Mapping (std::map) from filenames to stuff
        # calling s.GetMapping(full filename) returns a TagToValue
        # which we convert for our own use with a PythonTagToValue
        #pttv = gdcm.PythonTagToValue(mapping)

        # what i want:
        # a list of studies (indexed on study id): each study object
        # contains metadata we want to list per study, plus a list of
        # series belonging to that study.

        # maps from study_uid to instance of Study
        study_dict = {} 

        for f in filenames:
            mapping = s.GetMapping(f)

            # with this we can iterate through all tags for this file
            # let's store them all...
            file_tags = {}
            pttv = gdcm.PythonTagToValue(mapping)
            pttv.Start()
            while not pttv.IsAtEnd():
                tag = pttv.GetCurrentTag() # gdcm::Tag
                val = pttv.GetCurrentValue() # string

                symbol = tag_to_symbol[(tag.GetGroup(), tag.GetElement())]
                file_tags[symbol] = val

                pttv.Next()

            # take information from file_tags, stuff into all other
            # structures...

            # we need at least study and series UIDs to continue
            if not ('study_uid' in file_tags and \
                    'series_uid' in file_tags):
                continue
            
            study_uid = file_tags['study_uid']
            series_uid = file_tags['series_uid']
           
            # create a new study if it doesn't exist yet
            try:
                study = study_dict[study_uid]
            except KeyError:
                study = Study()
                study.uid = study_uid

                study.description = file_tags.get(
                        'study_description', '')
                study.date = file_tags.get(
                        'study_date', '')
                study.patient_name = file_tags.get(
                        'patient_name', '')
                study.patient_id = file_tags.get(
                        'patient_id', '')

                study_dict[study_uid] = study

            try:
                series = study.series_dict[series_uid]
            except KeyError:
                series = Series()
                series.uid = series_uid
                # these should be the same over the whole series
                series.description = \
                    file_tags.get('series_description', '')
                series.modality = file_tags.get('modality', '')

                series.rows = int(file_tags.get('rows', 0))
                series.columns = int(file_tags.get('columns', 0))

                study.series_dict[series_uid] = series

            series.filenames.append(f)

            
            try:
                number_of_frames = int(file_tags['number_of_frames'])
            except KeyError:
                # means number_of_frames wasn't found
                number_of_frames = 1

            series.slices = series.slices + number_of_frames
            study.slices = study.slices + number_of_frames

        return study_dict

    def _setup_image_viewer(self):
        # FIXME: I'm planning to factor this out into a medical image
        # viewing class, probably in the GDCM_KIT

        # setup VTK viewer with dummy source (else it complains)
        self._image_viewer = vtkgdcm.vtkImageColorViewer()
        self._image_viewer.SetupInteractor(self._view_frame.image_pane.rwi)
        ds = vtk.vtkImageGridSource()
        self._image_viewer.SetInput(ds.GetOutput())

        def setup_text_actor(x, y):
            ta = vtk.vtkTextActor()

            c = ta.GetPositionCoordinate()
            c.SetCoordinateSystemToNormalizedDisplay()
            c.SetValue(x,y)

            p = ta.GetTextProperty()
            p.SetFontFamilyToArial()
            p.SetFontSize(14)
            p.SetBold(0)
            p.SetItalic(0)
            p.SetShadow(0)

            return ta

        ren = self._image_viewer.GetRenderer()

        # direction labels left and right #####
        xl = self._image_viewer.xl_text_actor = setup_text_actor(0.01, 0.5)
        ren.AddActor(xl)
        xr = self._image_viewer.xr_text_actor = setup_text_actor(0.99, 0.5)
        xr.GetTextProperty().SetJustificationToRight()
        ren.AddActor(xr)

        # direction labels top and bottom #####
        # y coordinate ~ 0, bottom of normalized display
        yb = self._image_viewer.yb_text_actor = setup_text_actor(
                0.5, 0.01)
        ren.AddActor(yb)

        yt = self._image_viewer.yt_text_actor = setup_text_actor(
                0.5, 0.99)
        yt.GetTextProperty().SetVerticalJustificationToTop()
        ren.AddActor(yt)
                
        # labels upper-left #####
        ul = self._image_viewer.ul_text_actor = \
            setup_text_actor(0.01, 0.99)
        ul.GetTextProperty().SetVerticalJustificationToTop()
        ren.AddActor(ul)

        # labels upper-right #####
        ur = self._image_viewer.ur_text_actor = \
            setup_text_actor(0.99, 0.99)
        ur.GetTextProperty().SetVerticalJustificationToTop()
        ur.GetTextProperty().SetJustificationToRight()
        ren.AddActor(ur)

        # labels bottom-right #####
        br = self._image_viewer.br_text_actor = \
            setup_text_actor(0.99, 0.01)
        br.GetTextProperty().SetVerticalJustificationToBottom()
        br.GetTextProperty().SetJustificationToRight()
        ren.AddActor(br)
       


        

