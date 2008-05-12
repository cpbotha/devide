# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

import cStringIO
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor
import wx
import wx.aui
# need listmix.ColumnSorterMixin
import wx.lib.mixins.listctrl as listmix
from wx import BitmapFromImage, ImageFromStream

from resources.python import DICOMBrowserPanels
reload(DICOMBrowserPanels)

class StudyColumns:
    patient = 0
    patient_id = 1
    description = 2
    date = 3
    num_images = 4
    num_series = 5

class SeriesColumns:
    description = 0
    modality = 1
    num_images = 2
    row_col = 3

class FilesColumns:
    name = 0


#----------------------------------------------------------------------
def getSmallUpArrowData():
    return \
'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\
\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\
\x00\x00<IDAT8\x8dcddbf\xa0\x040Q\xa4{h\x18\xf0\xff\xdf\xdf\xffd\x1b\x00\xd3\
\x8c\xcf\x10\x9c\x06\xa0k\xc2e\x08m\xc2\x00\x97m\xd8\xc41\x0c \x14h\xe8\xf2\
\x8c\xa3)q\x10\x18\x00\x00R\xd8#\xec\xb2\xcd\xc1Y\x00\x00\x00\x00IEND\xaeB`\
\x82' 

def getSmallUpArrowBitmap():
    return BitmapFromImage(getSmallUpArrowImage())

def getSmallUpArrowImage():
    stream = cStringIO.StringIO(getSmallUpArrowData())
    return ImageFromStream(stream)

#----------------------------------------------------------------------
def getSmallDnArrowData():
    return \
"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\
\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\
\x00\x00HIDAT8\x8dcddbf\xa0\x040Q\xa4{\xd4\x00\x06\x06\x06\x06\x06\x16t\x81\
\xff\xff\xfe\xfe'\xa4\x89\x91\x89\x99\x11\xa7\x0b\x90%\ti\xc6j\x00>C\xb0\x89\
\xd3.\x10\xd1m\xc3\xe5*\xbc.\x80i\xc2\x17.\x8c\xa3y\x81\x01\x00\xa1\x0e\x04e\
?\x84B\xef\x00\x00\x00\x00IEND\xaeB`\x82" 

def getSmallDnArrowBitmap():
    return BitmapFromImage(getSmallDnArrowImage())

def getSmallDnArrowImage():
    stream = cStringIO.StringIO(getSmallDnArrowData())
    return ImageFromStream(stream)

#----------------------------------------------------------------------


class SortedListCtrl(wx.ListCtrl, listmix.ColumnSorterMixin):

    def __init__(self, parent, ID, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        
        # for the ColumnSorterMixin: this should be a dict mapping
        # from item data values to sequence of values for the columns.
        # These values will be used for sorting
        self.itemDataMap = {}

        self.il = wx.ImageList(16, 16)
        self.sm_up = self.il.Add(getSmallUpArrowBitmap())
        self.sm_dn = self.il.Add(getSmallDnArrowBitmap())
        self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

        listmix.ColumnSorterMixin.__init__(self, 5)

    def GetListCtrl(self):
        """Method required by ColumnSorterMixin.
        """
        return self

    def GetSortImages(self):
        """Used by the ColumnSorterMixin.
        """
        return (self.sm_dn, self.sm_up)

    def auto_size_columns(self):
        for idx in range(self.GetColumnCount()):
            self.SetColumnWidth(idx, wx.LIST_AUTOSIZE)

class SortedAutoWidthListCtrl(listmix.ListCtrlAutoWidthMixin, SortedListCtrl):
    def __init__(self, parent, ID, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):

        SortedListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)

class DICOMBrowserFrame(wx.Frame):
    def __init__(self, parent, id=-1, title="", name=""):
        wx.Frame.__init__(self, parent, id=id, title=title, 
                pos=wx.DefaultPosition, size=(800,800), name=name)


        self.menubar = wx.MenuBar()
        self.SetMenuBar(self.menubar)

        nav_menu = wx.Menu()
        self.id_next_image = wx.NewId()
        nav_menu.Append(self.id_next_image, "&Next image\tCtrl-N",
                "Go to next image in series", wx.ITEM_NORMAL)

        self.id_prev_image = wx.NewId()
        nav_menu.Append(self.id_prev_image, "&Previous image\tCtrl-P",
                "Go to previous image in series", wx.ITEM_NORMAL)

        self.menubar.Append(nav_menu, "&Navigation")
       

        views_menu = wx.Menu()
        views_default_id = wx.NewId()
        views_menu.Append(views_default_id, "&Default\tCtrl-0",
                         "Activate default view layout.", wx.ITEM_NORMAL)
                

        views_max_image_id = wx.NewId()
        views_menu.Append(views_max_image_id, "&Maximum image size\tCtrl-1",
                         "Activate maximum image view size layout.", 
                         wx.ITEM_NORMAL)

        self.menubar.Append(views_menu, "&Views")



        # tell FrameManager to manage this frame        
        self._mgr = wx.aui.AuiManager()
        self._mgr.SetManagedWindow(self)

        

        self._mgr.AddPane(self._create_dirs_pane(), wx.aui.AuiPaneInfo().
                          Name("dirs").
                          Caption("Files and Directories to Scan").
                          Top().Row(0).
                          Top().
                          CloseButton(False).MaximizeButton(True))

        self._mgr.AddPane(self._create_studies_pane(), wx.aui.AuiPaneInfo().
                          Name("studies").Caption("Studies").
                          Top().Row(1).
                          BestSize(wx.Size(600, 100)).
                          CloseButton(False).MaximizeButton(True))

        self._mgr.AddPane(self._create_series_pane(), wx.aui.AuiPaneInfo().
                          Name("series").Caption("Series").Top().Row(2).
                          BestSize(wx.Size(600, 100)).
                          CloseButton(False).MaximizeButton(True))

        self._mgr.AddPane(self._create_files_pane(), wx.aui.AuiPaneInfo().
                          Name("files").Caption("Image Files").
                          Left().
                          BestSize(wx.Size(200,400)).
                          CloseButton(False).MaximizeButton(True))

        self._mgr.AddPane(self._create_meta_pane(), wx.aui.AuiPaneInfo().
                          Name("meta").Caption("Image Metadata").
                          Left().
                          BestSize(wx.Size(200,400)).
                          CloseButton(False).MaximizeButton(True))

        self._mgr.AddPane(self._create_image_pane(), wx.aui.AuiPaneInfo().
                          Name("image").Caption("Image").
                          Center().
                          BestSize(wx.Size(400,400)).
                          CloseButton(False).MaximizeButton(True))



        self.SetMinSize(wx.Size(400, 300))

        self._perspectives = {} 
        self._perspectives['default'] = self._mgr.SavePerspective()

        self._mgr.GetPane("dirs").Hide()
        self._mgr.GetPane("studies").Hide()
        self._mgr.GetPane("series").Hide()
        self._mgr.GetPane("files").Hide()
        self._mgr.GetPane("meta").Hide()

        self._perspectives['max_image'] = self._mgr.SavePerspective()

        self._mgr.LoadPerspective(self._perspectives['default'])

        self._mgr.Update()

        # we bind the views events here, because the functionality is
        # completely encapsulated in the frame and does not need to
        # round-trip to the DICOMBrowser main module.
        self.Bind(wx.EVT_MENU, lambda e: self._mgr.LoadPerspective(
            self._perspectives['default']), id=views_default_id)

        self.Bind(wx.EVT_MENU, lambda e: self._mgr.LoadPerspective(
            self._perspectives['max_image']), id=views_max_image_id)


    def close(self):
        del self.dirs_pane
        del self.studies_lc
        del self.series_lc
        del self.files_lc
        self.Destroy()

    def _create_dirs_pane(self):
        # instantiate the wxGlade-created frame
        fpf = DICOMBrowserPanels.FilesPanelFrame(self, id=-1,
                size=(200, 150))
        # reparent the panel to us
        panel = fpf.files_panel
        panel.Reparent(self)

        # still need fpf.* to bind everything
        # but we can destroy fpf (everything has been reparented)
        fpf.Destroy()

        panel.ad_button = fpf.ad_button
        panel.af_button = fpf.af_button
        panel.scan_button = fpf.scan_button
        panel.dirs_files_tc = fpf.dirs_files_tc
        self.dirs_pane = panel

        return panel

    def _create_files_pane(self):
        sl = SortedListCtrl(self, -1, 
                style=wx.LC_REPORT)
        sl.InsertColumn(FilesColumns.name, "Full name")
        # we'll autosize this column later
        sl.SetColumnWidth(FilesColumns.name, 300)

        #sl.InsertColumn(SeriesColumns.modality, "Modality")

        self.files_lc = sl

        return sl

    def _create_image_pane(self):
        # instantiate the wxGlade-created frame
        ipf = DICOMBrowserPanels.ImagePanelFrame(self, id=-1,
                size=(400, 300))
        # reparent the panel to us
        panel = ipf.image_panel
        panel.Reparent(self)

        # still need fpf.* to bind everything
        # but we can destroy fpf (everything has been reparented)
        ipf.Destroy()

        panel.rwi = ipf.rwi
        panel.lock_pz_cb = ipf.lock_pz_cb
        panel.lock_wl_cb = ipf.lock_wl_cb
        panel.reset_b = ipf.reset_b

        self.image_pane = panel

        return panel

    def _create_meta_pane(self):
        ml = SortedAutoWidthListCtrl(self, -1, 
                style=wx.LC_REPORT | 
                wx.LC_HRULES | wx.LC_VRULES |
                wx.LC_SINGLE_SEL)

        ml.InsertColumn(0, "Key")
        ml.SetColumnWidth(0, 70)

        ml.InsertColumn(1, "Value")
        ml.SetColumnWidth(1, 70)

        self.meta_lc = ml

        return ml

    def _create_studies_pane(self):
        sl = SortedAutoWidthListCtrl(self, -1, 
                style=wx.LC_REPORT | 
                wx.LC_HRULES | 
                wx.LC_SINGLE_SEL)

        sl.InsertColumn(StudyColumns.patient, "Patient")
        sl.SetColumnWidth(StudyColumns.patient, 170)

        sl.InsertColumn(StudyColumns.patient_id, "Patient ID")
        sl.SetColumnWidth(StudyColumns.patient_id, 100)

        sl.InsertColumn(StudyColumns.description, "Description") 
        sl.SetColumnWidth(StudyColumns.description, 170)

        sl.InsertColumn(StudyColumns.date, "Date") # study date
        sl.SetColumnWidth(StudyColumns.date, 70)

        # total number of images
        sl.InsertColumn(StudyColumns.num_images, "# Images") 
        sl.InsertColumn(StudyColumns.num_series, "# Series") 

        self.studies_lc = sl

        return sl

    def _create_series_pane(self):
        sl = SortedAutoWidthListCtrl(self, -1, 
                style=wx.LC_REPORT | wx.LC_HRULES | wx.LC_SINGLE_SEL,
                size=(600,120))
        sl.InsertColumn(SeriesColumns.description, "Description")
        sl.SetColumnWidth(SeriesColumns.description, 170)

        sl.InsertColumn(SeriesColumns.modality, "Modality")
        sl.InsertColumn(SeriesColumns.num_images, "# Images")
        sl.InsertColumn(SeriesColumns.row_col, "Size")

        self.series_lc = sl

        return sl

    def render_image(self):
        """Update embedded RWI, i.e. update the image.
        """
        self.image_pane.rwi.Render()
       


