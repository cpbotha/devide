# $Id: dicomRDR.py,v 1.2 2003/02/08 01:02:34 cpbotha Exp $

import gen_utils
import os
from moduleBase import moduleBase
from moduleMixins import \
     vtkPipelineConfigModuleMixin, fileOpenDialogModuleMixin

import stat
from wxPython.wx import *
from wxPython.xrc import *
import vtk
import vtkdscas
import moduleUtils

class dicomRDR(moduleBase,
                    vtkPipelineConfigModuleMixin,
                    fileOpenDialogModuleMixin):
    
    def __init__(self, moduleManager):
        # call the constructor in the "base"
        moduleBase.__init__(self, moduleManager)

        # setup necessary VTK objects
	self._reader = vtkdscas.vtkDICOMVolumeReader()

        # this part of the config is stored only in the config, and not in
        # the reader.
        self._config.dicom_dirname = None
        self._config.dicom_filenames = []

        self._viewFrame = None
        self._createViewFrame()

        # do the normal thang (down to logic, up again)
        self.configToLogic()
        self.syncViewWithLogic()

	# display it
        self.view()
	
    def close(self):
        self._viewFrame.Destroy()
        del self._reader

    def getInputDescriptions(self):
	return ()
    
    def setInput(self, idx, input_stream):
	raise Exception
    
    def getOutputDescriptions(self):
	return (self._reader.GetOutput().GetClassName(),)
    
    def getOutput(self, idx):
	return self._reader.GetOutput()


    def logicToConfig(self):
        pass # FIXME: continue here
    
    def sync_config(self):
        # get our internal dirname (what use is this; it'll never change...
        # we also probably can't query the dirname from the DICOM reader
        if self._dicom_dirname:
            self._viewFrame.dirname_text.SetValue(self._dicom_dirname)
        else:
            self._viewFrame.dirname_text.SetValue("")

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
        self._viewFrame.dimensions_text.SetValue('%s at %s mm' %
                                                  (str(dd), str(ds)))
        

	
    def apply_config(self):
        # get a list of files in the indicated directory, stuff them all
        # into the dicom reader
        self._dicom_dirname = self._viewFrame.dirname_text.GetValue()

        if self._dicom_dirname == None or self._dicom_dirname == "":
            return
        try:
            filenames_init = os.listdir(self._dicom_dirname)
        except Exception, e:
            gen_utils.log_error('Could not read DICOM directory: %s' % e)

        # go through list of files in directory, perform trivial tests
        # and create a new list of files 
        dicom_fullnames = []
        for filename in filenames_init:
            # make full filename
            fullname = os.path.join(self._dicom_dirname, filename)
            # at the moment, we check that it's a regular file
            if stat.S_ISREG(os.stat(fullname)[stat.ST_MODE]):
                dicom_fullnames.append(fullname)

        if len(dicom_fullnames) == 0:
            wxLogError('Empty directory specified, not attempting '
                       'change in config.')
            return

        # this will clear only the dicom_filenames_buffer without setting
        # mtime of the vtkDICOMVolumeReader
        self._reader.clear_dicom_filenames()

        for fullname in dicom_fullnames:
            # this will simply add a file to the buffer list of the
            # vtkDICOMVolumeReader (will not set mtime)
            print "%s\n" % fullname
            self._reader.add_dicom_filename(fullname)
        
        # if we've added the same list as we added at the previous exec
        # of apply_config(), the dicomreader is clever enough to know that
        # it doesn't require an update.  Yay me.

        # also apply the SeriesInstanceIDX
        self._reader.SetSeriesInstanceIdx(
            self._viewFrame.si_idx_spin.GetValue())

        # we perform this call, as it will result in an ExecuteInfo of the
        # DICOMReader, thus yielding bunches of interesting information
        self.sync_config()

    def execute_module(self):
        self._reader.SetProgressText('Reading DICOM data')
        mm = self._moduleManager
        self._reader.SetProgressMethod(lambda s=self, mm=mm:
                                       mm.vtk_progress_cb(s._reader))
        
        # get the vtkDICOMVolumeReader to try and execute
	self._reader.Update()
        # tell the vtk log file window to poll the file; if the file has
        # changed, i.e. vtk has written some errors, the log window will
        # pop up.  you should do this in all your modules right after you
        # caused some VTK processing which might have resulted in VTK
        # outputting to the error log
        self._moduleManager.vtk_poll_error()

    def _createViewFrame(self):
        import modules.resources.python.dicomRDRViewFrame
        reload(modules.resources.python.dicomRDRViewFrame)
        
        parent_window = self._moduleManager.get_module_view_parent_window()
        self._viewFrame = modules.resources.python.dicomRDRViewFrame.\
                          dicomRDRViewFrame(parent_window, id=-1,
                                            title='dummy')
        
        EVT_CLOSE(self._viewFrame,
                  lambda e, s=self: s._viewFrame.Show(false))

        EVT_BUTTON(self._viewFrame, self._viewFrame.BROWSE_BUTTON_ID,
                   self.dn_browse_cb)
        EVT_CHOICE(self._viewFrame, self._viewFrame.VTK_OBJECT_CHOICE_ID,
                   self.vtk_object_choice_cb)
        EVT_BUTTON(self._viewFrame, self._viewFrame.VTK_PIPELINE_ID,
                   self.vtk_pipeline_cb)

        module_utils.bind_CSAEO2(self, self._viewFrame)

        # bind events to the standard cancel, sync, apply, execute, ok buttons
#        module_utils.bind_CSAEO(self, self._viewFrame)



    def view(self, parent_window=None):
	# first make sure that our variables agree with the stuff that
        # we're configuring
	self.sync_config()
        self._viewFrame.Show(true)
        
    def dn_browse_cb(self, event):
        path = self.dn_browse(self._viewFrame,
                              "Choose a DICOM directory",
                              self._moduleManager.get_app_dir())

        if path != None:
            self._viewFrame.dirname_text.SetValue(path)

    def vtk_object_choice_cb(self, event):
        if self._viewFrame.object_choice.GetStringSelection() == \
           'vtkDICOMVolumeReader':
            self.vtk_object_configure(self._viewFrame, None, self._reader)

    def vtk_pipeline_cb(self, event):
        # move this to module utils too, or to base...
        self.vtk_pipeline_configure(self._viewFrame, None, (self._reader,))
	    
