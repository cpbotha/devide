# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

import genUtils
from module_kits.misc_kit import misc_utils
import os
from module_base import ModuleBase
from moduleMixins import \
     IntrospectModuleMixin, FileOpenDialogModuleMixin
import module_utils


import stat
import wx
import vtk
import vtkdevide
import module_utils

class dicomRDR(ModuleBase,
               IntrospectModuleMixin,
               FileOpenDialogModuleMixin):

    def __init__(self, module_manager):
        # call the constructor in the "base"
        ModuleBase.__init__(self, module_manager)

        # setup necessary VTK objects
        self._reader = vtkdevide.vtkDICOMVolumeReader()

        module_utils.setupVTKObjectProgress(self, self._reader,
                                           'Reading DICOM data')
        

        self._viewFrame = None

        self._fileDialog = None

        # setup some defaults
        self._config.dicomFilenames = []
        self._config.seriesInstanceIdx = 0
        self._config.estimateSliceThickness = 1

        # do the normal thang (down to logic, up again)
        self.sync_module_logic_with_config()
	
    def close(self):
        if self._fileDialog is not None:
            del self._fileDialog
            
        # this will take care of all the vtkPipeline windows
        IntrospectModuleMixin.close(self)

        if self._viewFrame is not None:
            # take care of our own window
            self._viewFrame.Destroy()
            
        # also remove the binding we have to our reader
        del self._reader

    def get_input_descriptions(self):
        return ()
    
    def set_input(self, idx, input_stream):
        raise Exception
    
    def get_output_descriptions(self):
        return ('DICOM data (vtkStructuredPoints)',)
    
    def get_output(self, idx):
        return self._reader.GetOutput()


    def logic_to_config(self):
        self._config.seriesInstanceIdx = self._reader.GetSeriesInstanceIdx()
        # refresh our list of dicomFilenames
        del self._config.dicomFilenames[:]
        for i in range(self._reader.get_number_of_dicom_filenames()):
            self._config.dicomFilenames.append(
                self._reader.get_dicom_filename(i))

        self._config.estimateSliceThickness = self._reader.\
                                              GetEstimateSliceThickness()
        

    def config_to_logic(self):
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


    def view_to_config(self):
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


    def config_to_view(self):
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

    
    def execute_module(self):
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

        xl = misc_utils.major_axis_from_iop_cosine(row)
        yl = misc_utils.major_axis_from_iop_cosine(col)
        zl = misc_utils.major_axis_from_iop_cosine(norm)

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

        self._viewFrame = module_utils.instantiateModuleViewFrame(
            self, self._module_manager,
            modules.readers.resources.python.dicomRDRViewFrame.\
            dicomRDRViewFrame)

        # make sure the listbox is empty
        self._viewFrame.dicomFilesListBox.Clear()

        objectDict = {'dicom reader' : self._reader}
        module_utils.createStandardObjectAndPipelineIntrospection(
            self, self._viewFrame, self._viewFrame.viewFramePanel,
            objectDict, None)

        module_utils.createECASButtons(self, self._viewFrame,
                                      self._viewFrame.viewFramePanel)

        wx.EVT_BUTTON(self._viewFrame, self._viewFrame.addButton.GetId(),
                      self._handlerAddButton)

        wx.EVT_BUTTON(self._viewFrame, self._viewFrame.removeButton.GetId(),
                      self._handlerRemoveButton)

        # follow ModuleBase convention to indicate that we now have
        # a view
        self.view_initialised = True
        
        

    def view(self, parent_window=None):
        if self._viewFrame is None:
            self._createViewFrame()
            self.sync_module_view_with_logic()
            
        self._viewFrame.Show(True)
        self._viewFrame.Raise()
        
    def _handlerAddButton(self, event):

        if not self._fileDialog:
            self._fileDialog = wx.FileDialog(
                self._module_manager.getModuleViewParentWindow(),
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

            
