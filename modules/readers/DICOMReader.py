# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

from moduleBase import moduleBase
from module_kits.misc_kit import misc_utils
from moduleMixins import \
     introspectModuleMixin
import moduleUtils

import gdcm
import vtk
import vtkgdcm
import wx

from module_kits.misc_kit.devide_types import MedicalMetaData

class DRDropTarget(wx.PyDropTarget):
    def __init__(self, dicom_reader):
        wx.PyDropTarget.__init__(self)
        self._fdo = wx.FileDataObject()
        self.SetDataObject(self._fdo)
        self._dicom_reader = dicom_reader

    def OnDrop(self, x, y):
        return True

    def OnData(self, x, y, d):
        if self.GetData():
            filenames = self._fdo.GetFilenames()
            lb = self._dicom_reader._view_frame.dicom_files_lb
            lb.Clear()
            lb.AppendItems(filenames)

        return d

class DICOMReader(introspectModuleMixin, moduleBase):
    def __init__(self, module_manager):
        moduleBase.__init__(self, module_manager)

        self._reader = vtkgdcm.vtkGDCMImageReader()
        # NB NB NB: for now we're SWITCHING off the VTK-compatible
        # Y-flip, until the X-mirror issues can be solved.
        self._reader.SetFileLowerLeft(1)
        self._ici = vtk.vtkImageChangeInformation()
        self._ici.SetInputConnection(0, self._reader.GetOutputPort(0))

        # create output MedicalMetaData and populate it with the
        # necessary bindings.
        mmd = MedicalMetaData()
        mmd.medical_image_properties = \
                self._reader.GetMedicalImageProperties()
        mmd.direction_cosines = \
                self._reader.GetDirectionCosines()
        self._output_mmd = mmd

        moduleUtils.setupVTKObjectProgress(self, self._reader,
                                           'Reading DICOM data')

        self._view_frame = None
        self._file_dialog = None
        self._config.dicom_filenames = []

        self.sync_module_logic_with_config()

    def close(self):
        introspectModuleMixin.close(self)

        # we just delete our binding.  Destroying the view_frame
        # should also take care of this one.
        del self._file_dialog

        if self._view_frame is not None:
            self._view_frame.Destroy()

        self._output_mmd.close() 
        del self._output_mmd

        del self._reader

        moduleBase.close(self) 


    def get_input_descriptions(self):
        return ()
    
    def set_input(self, idx, input_stream):
        raise Exception
    
    def get_output_descriptions(self):
        return ('DICOM data (vtkStructuredPoints)',
                'Medical Meta Data')
    
    def get_output(self, idx):
        if idx == 0:
            return self._ici.GetOutput()
        elif idx == 1:
            return self._output_mmd

    def logic_to_config(self):
        # we deliberately don't do any processing here, as we want to
        # limit all DICOM parsing to the execute_module
        pass

    def config_to_logic(self):
        # we deliberately don't add filenames to the reader here, as
        # we would need to sort them, which would imply scanning all
        # of them during this step

        # we return False to indicate that we haven't made any changes
        # to the underlying logic (so that the MetaModule knows it
        # doesn't have to invalidate us after a call to
        # config_to_logic)
        return False

    def view_to_config(self):
        lb = self._view_frame.dicom_files_lb
        
        # just clear out the current list
        # and copy everything, only if necessary!
        if self._config.dicom_filenames[:] == lb.GetStrings()[:]:
            return False
        else:
            self._config.dicom_filenames[:] = lb.GetStrings()[:]
            return True

    def config_to_view(self):
        # get listbox, clear it out, add filenames from the config
        lb = self._view_frame.dicom_files_lb
        if self._config.dicom_filenames[:] != lb.GetStrings()[:]:
            lb.Clear()
            lb.AppendItems(self._config.dicom_filenames)
    
    def execute_module(self):
        # have to  cast to normal strings (from unicode)
        filenames = [str(i) for i in self._config.dicom_filenames]

        # make sure all is zeroed.
        self._reader.SetFileName(None)
        self._reader.SetFileNames(None)

        # we only sort and derive slice-based spacing if there are
        # more than 1 filenames
        if len(filenames) > 1:
            sorter = gdcm.IPPSorter()
            sorter.SetComputeZSpacing(True)
            sorter.SetZSpacingTolerance(1e-2)

            ret = sorter.Sort(filenames)
            if not ret:
                raise RuntimeError(
                'Could not sort DICOM filenames before loading.')

            if sorter.GetZSpacing() == 0.0:
                msg = 'DICOM IPP sorting yielded incorrect results.'
                raise RuntimeError(msg)

            # then give the reader the sorted list of files
            sa = vtk.vtkStringArray()
            for fn in sorter.GetFilenames(): 
                sa.InsertNextValue(fn)

            self._reader.SetFileNames(sa)

        elif len(filenames) == 1:
            self._reader.SetFileName(filenames[0])

        else:
            raise RuntimeError(
                    'No DICOM filenames to read.')

        # now do the actual reading
        self._reader.Update()

        # see what the reader thinks the spacing is
        spacing = list(self._reader.GetDataSpacing())

        if len(filenames) > 1:
            # after the reader has done its thing,
            # impose derived spacing on the vtkImageChangeInformation
            # (by default it takes the SpacingBetweenSlices, which is
            # not always correct)
            spacing[2] = sorter.GetZSpacing()
            print "SPACING", sorter.GetZSpacing()

        # single or multiple filenames, we have to set the correct
        # output spacing on the image change information
        self._ici.SetOutputSpacing(spacing)
        self._ici.Update()


        # integrate DirectionCosines into output data ###############
        # DirectionCosines: first two columns are X and Y in the RAH
        # space
        dc = self._reader.GetDirectionCosines()

        x_cosine = \
                dc.GetElement(0,0), dc.GetElement(1,0), dc.GetElement(2,0)
        y_cosine = \
                dc.GetElement(0,1), dc.GetElement(1,1), dc.GetElement(2,1)

        # calculate plane normal, also in RAH space
        norm = [0,0,0]
        vtk.vtkMath.Cross(x_cosine, y_cosine, norm)

        xl = misc_utils.major_axis_from_iop_cosine(x_cosine)
        yl = misc_utils.major_axis_from_iop_cosine(y_cosine)

        # vtkGDCMImageReader swaps the y (to fit the VTK convention),
        # but does not flip the DirectionCosines here, so we do that.
        # (only if the reader is flipping)
        if yl and not self._reader.GetFileLowerLeft():
            yl = tuple((yl[1], yl[0]))

        zl = misc_utils.major_axis_from_iop_cosine(norm)

        lut = {'L' : 0, 'R' : 1, 'P' : 2, 'A' : 3, 'F' : 4, 'H' : 5}
    
        if xl and yl and zl:
            # add this data as a vtkFieldData
            fd = self._ici.GetOutput().GetFieldData()

            axis_labels_array = vtk.vtkIntArray()
            axis_labels_array.SetName('axis_labels_array')

            for l in xl + yl + zl:
                axis_labels_array.InsertNextValue(lut[l])

            fd.AddArray(axis_labels_array)

        

    def _create_view_frame(self):
        import modules.readers.resources.python.DICOMReaderViewFrame
        reload(modules.readers.resources.python.DICOMReaderViewFrame)

        self._view_frame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager,
            modules.readers.resources.python.DICOMReaderViewFrame.\
            DICOMReaderViewFrame)

        # make sure the listbox is empty
        self._view_frame.dicom_files_lb.Clear()

        object_dict = {
                'Module (self)'      : self,
                'vtkGDCMImageReader' : self._reader}
        moduleUtils.createStandardObjectAndPipelineIntrospection(
            self, self._view_frame, self._view_frame.view_frame_panel,
            object_dict, None)

        moduleUtils.createECASButtons(self, self._view_frame,
                                      self._view_frame.view_frame_panel)

        # now add the event handlers
        self._view_frame.add_files_b.Bind(wx.EVT_BUTTON,
                self._handler_add_files_b)
        self._view_frame.remove_files_b.Bind(wx.EVT_BUTTON,
                self._handler_remove_files_b)

        # also the drop handler
        dt = DRDropTarget(self)
        self._view_frame.dicom_files_lb.SetDropTarget(dt)


        # follow moduleBase convention to indicate that we now have
        # a view
        self.view_initialised = True

    def view(self, parent_window=None):
        if self._view_frame is None:
            self._create_view_frame()
            self.sync_module_view_with_logic()
            
        self._view_frame.Show(True)
        self._view_frame.Raise()

    def _add_filenames_to_listbox(self, filenames):
        # only add filenames that are not in there yet...
        lb = self._view_frame.dicom_files_lb

        # create new dictionary with current filenames as keys
        dup_dict = {}.fromkeys(lb.GetStrings(), 1)

        fns_to_add = [fn for fn in filenames
                      if fn not in dup_dict]

        lb.AppendItems(fns_to_add)

    def _handler_add_files_b(self, event):
        if not self._file_dialog:
            self._file_dialog = wx.FileDialog(
                self._view_frame,
                'Select files to add to the list', "", "",
                "DICOM files (*.dcm)|*.dcm|All files (*)|*",
                wx.OPEN | wx.MULTIPLE)
            
        if self._file_dialog.ShowModal() == wx.ID_OK:
            new_filenames = self._file_dialog.GetPaths()
            self._add_filenames_to_listbox(new_filenames)


    def _handler_remove_files_b(self, event):
        lb = self._view_frame.dicom_files_lb
        sels = list(lb.GetSelections())

        # we have to delete from the back to the front
        sels.sort()
        sels.reverse()

        for sel in sels:
            lb.Delete(sel)

