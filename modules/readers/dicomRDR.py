# $Id$

import genUtils
import os
from moduleBase import moduleBase
from moduleMixins import \
     vtkPipelineConfigModuleMixin, fileOpenDialogModuleMixin
import moduleUtils


import stat
import wx
import vtk
import vtkdevide
import moduleUtils

class dicomRDR(moduleBase,
               vtkPipelineConfigModuleMixin,
               fileOpenDialogModuleMixin):

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

    def _major_axis_from_iop_cosine(self, iop_cosine):
        """Given an IOP direction cosine, i.e. either the row or column,
        return a tuple with two components from LRPAFH signifying the
        direction of the cosine.  For example, if the cosine is pointing from
        Left to Right (1\0\0) we return ('L', 'R').

        If the direction cosine is NOT aligned with any of the major axes,
        we return None.

        Based on a routine from dclunie's pixelmed software and info from
        http://www.itk.org/pipermail/insight-users/2003-September/004762.html
        but we've flipped some things around to make more sense.

        IOP direction cosines are always in the RAH system:
         * x is left to right
         * y is posterior to anterior
         * z is foot to head <-- seems this might be the other way around,
           judging by dclunie's code.
        """

        obliquity_threshold = 0.8

        orientation_x = [('L', 'R'), ('R', 'L')][int(iop_cosine[0] > 0)]
        orientation_y = [('P', 'A'), ('A', 'P')][int(iop_cosine[1] > 0)]
        orientation_z = [('H', 'F'), ('F', 'H')][int(iop_cosine[2] > 0)]

        abs_x = abs(iop_cosine[0])
        abs_y = abs(iop_cosine[1])
        abs_z = abs(iop_cosine[2])

        if abs_x > obliquity_threshold and abs_x > abs_y and abs_x > abs_z:
            return orientation_x

        elif abs_y > obliquity_threshold and abs_y > abs_x and abs_y > abs_z:
            return orientation_y

        elif abs_z > obliquity_threshold and abs_z > abs_x and abs_z > abs_y:
            return orientation_z

        else:
            return None
    
    def executeModule(self):
        # get the vtkDICOMVolumeReader to try and execute
	self._reader.Update()
        

        # now get some metadata out and insert it in our output stream

        # first determine axis labels based on IOP ####################
        iop = self._reader.GetImageOrientationPatient()
        row = iop[0:3]
        col = iop[3:6]
        # the cross product (plane normal) based on the row and col will
        # also be in the RAH system (I THINK)
        norm = [0,0,0]
        vtk.vtkMath.Cross(row, col, norm)

        xl = self._major_axis_from_iop_cosine(row)
        yl = self._major_axis_from_iop_cosine(col)
        zl = self._major_axis_from_iop_cosine(norm)

        lut = {'L' : 0, 'R' : 1, 'P' : 2, 'A' : 3, 'F' : 4, 'H' : 5}

        if xl and yl and zl:
            # add this data as a vtkFieldData
            fd = self._reader.GetOutput().GetFieldData()

            axis_labels_array = vtk.vtkIntArray()
            axis_labels_array.SetName('axis_labels_array')

            for l in xl + yl + zl:
                axis_labels_array.InsertNextValue(lut[l])

            fd.AddArray(axis_labels_array)

        # window/level ###############################################
        

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

            
