# $Id: dicomRDR.py,v 1.7 2003/02/17 23:07:17 cpbotha Exp $

import genUtils
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

        self._viewFrame = ""
        self._createViewFrame()

        # setup some defaults
        self._config.dicomDirname = ""
        self._config.dicomFilenames = []
        self._config.seriesInstanceIdx = -1

        # do the normal thang (down to logic, up again)
        self.configToLogic()
        self.syncViewWithLogic()

	# display it
        self.view()
	
    def close(self):
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
	return (self._reader.GetOutput().GetClassName(),)
    
    def getOutput(self, idx):
	return self._reader.GetOutput()


    def logicToConfig(self):
        self._config.seriesInstanceIdx = self._reader.GetSeriesInstanceIdx()
        # refresh our list of dicomFilenames
        del self._config.dicomFilenames[:]
        for i in range(self._reader.get_number_of_dicom_filenames()):
            self._config.dicomFilenames.append(
                self._reader.get_dicom_filename(i))

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


    def viewToConfig(self):
        self._config.seriesInstanceIdx = self._viewFrame.si_idx_spin.GetValue()
        self._config.dicomDirname = self._viewFrame.dirname_text.GetValue()

        # get a list of files in the indicated directory, stuff them all
        # into the config list
        if self._config.dicomDirname == None or \
           self._config.dicomDirname == "":
            return
        try:
            filenames_init = os.listdir(self._config.dicomDirname)
        except Exception, e:
            genUtils.logError('Could not read DICOM directory: %s' % e)
            return

        # go through list of files in directory, perform trivial tests
        # and create a new list of files 
        del self._config.dicomFilenames[:]
        for filename in filenames_init:
            # make full filename
            fullname = os.path.join(self._config.dicomDirname, filename)
            # at the moment, we check that it's a regular file
            if stat.S_ISREG(os.stat(fullname)[stat.ST_MODE]):
                self._config.dicomFilenames.append(fullname)

        if len(self._config.dicomFilenames) == 0:
            wxLogError('Empty directory specified, not attempting '
                       'change in config.')


    def configToView(self):
        # at this stage, we can always assume that the logic is current
        # with the config struct...

        self._viewFrame.si_idx_spin.SetValue(self._config.seriesInstanceIdx)
        self._viewFrame.dirname_text.SetValue(self._config.dicomDirname)

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
    
    
    def executeModule(self):
        # following is the standard way of connecting up the dscas3 progress
        # callback to a VTK object; you should do this for all objects in
        # your module - you could do this in __init__ as well, it seems
        # neater here though
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

        # indicate that we're done
        mm.setProgress(100, 'DONE Reading DICOM data')

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

        moduleUtils.bindCSAEO(self, self._viewFrame)

        # bind events to the standard cancel, sync, apply, execute, ok buttons
#        moduleUtils.bind_CSAEO(self, self._viewFrame)



    def view(self, parent_window=None):
        if not self._viewFrame.Show(true):
            self._viewFrame.Raise()
        
    def dn_browse_cb(self, event):
        path = self.dirnameBrowse(self._viewFrame,
                                  "Choose a DICOM directory",
                                  self._moduleManager.get_app_dir())

        if path != None:
            self._viewFrame.dirname_text.SetValue(path)

    def vtk_object_choice_cb(self, event):
        if self._viewFrame.object_choice.GetStringSelection() == \
           'vtkDICOMVolumeReader':
            self.vtkObjectConfigure(self._viewFrame, None, self._reader)

    def vtk_pipeline_cb(self, event):
        # move this to module utils too, or to base...
        self.vtkPipelineConfigure(self._viewFrame, None, (self._reader,))
	    
