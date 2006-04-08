# $Id$

import genUtils
import os
from moduleBase import moduleBase
from moduleMixins import \
     vtkPipelineConfigModuleMixin, fileOpenDialogModuleMixin
import moduleUtils
from module_kits.vtk_kit.mixins import VTKErrorFuncMixin

import stat
import wx
import vtk
import vtkdevide
import moduleUtils

class dicomRDR(moduleBase,
               vtkPipelineConfigModuleMixin,
               fileOpenDialogModuleMixin,
               VTKErrorFuncMixin):

    """Module for reading DICOM data.

    Add DICOM files (they may be from multiple series) by using the 'Add'
    button on the view/config window.  You can select multiple files in
    the File dialog by holding shift or control whilst clicking.

    $Revision: 1.12 $
    """
    
    def __init__(self, moduleManager):
        # call the constructor in the "base"
        moduleBase.__init__(self, moduleManager)

        # setup necessary VTK objects
	self._reader = vtkdevide.vtkDICOMVolumeReader()

        moduleUtils.setupVTKObjectProgress(self, self._reader,
                                           'Reading DICOM data')
        self.add_vtk_error_handler(self._reader)

        self._viewFrame = ""
        self._createViewFrame()

        self._fileDialog = None

        # setup some defaults
        self._config.dicomFilenames = []
        self._config.seriesInstanceIdx = 0
        self._config.estimateSliceThickness = 1

        # do the normal thang (down to logic, up again)
        self.configToLogic()
        self.logicToConfig()
        self.configToView()
	
    def close(self):
        del self._fileDialog
        # this will take care of all the vtkPipeline windows
        vtkPipelineConfigModuleMixin.close(self)
        # take care of our own window
        self._viewFrame.Destroy()
        # also remove the binding we have to our reader
        del self._reader

    def getInputDescriptions(self):
	return ()
    
    def setInput(self, idx, input_stream):
	raise Exception
    
    def getOutputDescriptions(self):
	return ('DICOM data (vtkStructuredPoints)',)
    
    def getOutput(self, idx):
	return self._reader.GetOutput()


    def logicToConfig(self):
        self._config.seriesInstanceIdx = self._reader.GetSeriesInstanceIdx()
        # refresh our list of dicomFilenames
        del self._config.dicomFilenames[:]
        for i in range(self._reader.get_number_of_dicom_filenames()):
            self._config.dicomFilenames.append(
                self._reader.get_dicom_filename(i))

        self._config.estimateSliceThickness = self._reader.\
                                              GetEstimateSliceThickness()
        

    def configToLogic(self):
        self._reader.SetSeriesInstanceIdx(self._config.seriesInstanceIdx)
        
        # this will clear only the dicom_filenames_buffer without setting
        # mtime of the vtkDICOMVolumeReader
        self._reader.clear_dicom_filenames()

        for fullname in self._config.dicomFilenames:
            # this will simply add a file to the buffer list of the
            # vtkDICOMVolumeReader (will not set mtime)
            self._reader.add_dicom_filename(fullname)
        
        # if we've added the same list as we added at the previous exec
        # of apply_config(), the dicomreader is clever enough to know that
        # it doesn't require an update.  Yay me.

        self._reader.SetEstimateSliceThickness(
            self._config.estimateSliceThickness)


    def viewToConfig(self):
        self._config.seriesInstanceIdx = self._viewFrame.si_idx_spin.GetValue()

        lb = self._viewFrame.dicomFilesListBox
        count = lb.GetCount()

        filenames_init = []
        for n in range(count):
            filenames_init.append(lb.GetString(n))
        
        # go through list of files in directory, perform trivial tests
        # and create a new list of files 
        del self._config.dicomFilenames[:]
        for filename in filenames_init:
            # at the moment, we check that it's a regular file
            if stat.S_ISREG(os.stat(filename)[stat.ST_MODE]):
                self._config.dicomFilenames.append(filename)

        if len(self._config.dicomFilenames) == 0:
            wx.LogError('Empty directory specified, not attempting '
                       'change in config.')

        self._config.estimateSliceThickness = self._viewFrame.\
                                              estimateSliceThicknessCheckBox.\
                                              GetValue()


    def configToView(self):
        # first transfer list of files to listbox
        lb = self._viewFrame.dicomFilesListBox
        lb.Clear()
        for fn in self._config.dicomFilenames:
            lb.Append(fn)
        
        # at this stage, we can always assume that the logic is current
        # with the config struct...
        self._viewFrame.si_idx_spin.SetValue(self._config.seriesInstanceIdx)

        # some information in the view does NOT form part of the config,
        # but comes directly from the logic:

        # we're going to be reading some information from the _reader which
        # is only up to date after this call
        self._reader.UpdateInformation()
        self.check_vtk_error()

        # get current SeriesInstanceIdx from the DICOMReader
        # FIXME: the frikking SpinCtrl does not want to update when we call
        # SetValue()... we've now hard-coded it in wxGlade (still doesn't work)
        self._viewFrame.si_idx_spin.SetValue(
            int(self._reader.GetSeriesInstanceIdx()))

        # try to get current SeriesInstanceIdx (this will run at least
        # UpdateInfo)
        si_uid = self._reader.GetSeriesInstanceUID()
        if si_uid == None:
            si_uid = "NONE"

        self._viewFrame.si_uid_text.SetValue(si_uid)

        msii = self._reader.GetMaximumSeriesInstanceIdx()
        self._viewFrame.seriesInstancesText.SetValue(str(msii))
        # also limit the spin-control
        self._viewFrame.si_idx_spin.SetRange(0, msii)

        sd = self._reader.GetStudyDescription()
        if sd == None:
            self._viewFrame.study_description_text.SetValue("NONE");
        else:
            self._viewFrame.study_description_text.SetValue(sd);

        rp = self._reader.GetReferringPhysician()
        if rp == None:
            self._viewFrame.referring_physician_text.SetValue("NONE");
        else:
            self._viewFrame.referring_physician_text.SetValue(rp);
            
            
        dd = self._reader.GetDataDimensions()
        ds = self._reader.GetDataSpacing()
        self._viewFrame.dimensions_text.SetValue(
            '%d x %d x %d at %.2f x %.2f x %.2f mm / voxel' % tuple(dd + ds))

        self._viewFrame.estimateSliceThicknessCheckBox.SetValue(
            self._config.estimateSliceThickness)
    
    def executeModule(self):
        # get the vtkDICOMVolumeReader to try and execute
	self._reader.Update()
        self.check_vtk_error()

    def _createViewFrame(self):
        import modules.readers.resources.python.dicomRDRViewFrame
        reload(modules.readers.resources.python.dicomRDRViewFrame)

        self._viewFrame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager,
            modules.readers.resources.python.dicomRDRViewFrame.\
            dicomRDRViewFrame)

        # make sure the listbox is empty
        self._viewFrame.dicomFilesListBox.Clear()

        objectDict = {'dicom reader' : self._reader}
        moduleUtils.createStandardObjectAndPipelineIntrospection(
            self, self._viewFrame, self._viewFrame.viewFramePanel,
            objectDict, None)

        moduleUtils.createECASButtons(self, self._viewFrame,
                                      self._viewFrame.viewFramePanel)

        wx.EVT_BUTTON(self._viewFrame, self._viewFrame.addButton.GetId(),
                      self._handlerAddButton)

        wx.EVT_BUTTON(self._viewFrame, self._viewFrame.removeButton.GetId(),
                      self._handlerRemoveButton)
        
        

    def view(self, parent_window=None):
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()
        
    def _handlerAddButton(self, event):

        if not self._fileDialog:
            self._fileDialog = wx.FileDialog(
                self._moduleManager.getModuleViewParentWindow(),
                'Select files to add to the list', "", "",
                "DICOM files (*.dcm)|*.dcm|All files (*)|*",
                wx.OPEN | wx.MULTIPLE)
            
        if self._fileDialog.ShowModal() == wx.ID_OK:
            newFilenames = self._fileDialog.GetPaths()

            # first check for duplicates in the listbox
            lb = self._viewFrame.dicomFilesListBox
            count = lb.GetCount()

            oldFilenames = []
            for n in range(count):
                oldFilenames.append(lb.GetString(n))

            filenamesToAdd = [fn for fn in newFilenames
                              if fn not in oldFilenames]

            for fn in filenamesToAdd:
                lb.Append(fn)

    def _handlerRemoveButton(self, event):
        """Remove all selected filenames from the internal list.
        """

        lb = self._viewFrame.dicomFilesListBox
        sels = list(lb.GetSelections())

        # we have to delete from the back to the front
        sels.sort()
        sels.reverse()

        # build list
        for sel in sels:
            lb.Delete(sel)

            
