# $Id: vtk_plydta_rdr.py,v 1.7 2002/05/19 14:29:41 cpbotha Exp $

from module_base import \
     module_base, \
     module_mixin_vtk_pipeline_config, \
     module_mixin_fo_dialog
from wxPython.wx import *
from wxPython.xrc import *
import vtk
import os
import module_utils

class vtk_plydta_rdr(module_base,
                     module_mixin_vtk_pipeline_config,
                     module_mixin_fo_dialog):
    
    def __init__(self, module_manager):
        # call the constructor in the "base"
        module_base.__init__(self, module_manager)

        # setup necessary VTK objects
	self._reader = vtk.vtkPolyDataReader()

        # following is the standard way of connecting up the dscas3 progress
        # callback to a VTK object; you should do this for all objects in
        # your module
        self._reader.SetProgressText('Reading VTK polydata')
        mm = self._module_manager
        self._reader.SetProgressMethod(lambda s=self, mm=mm:
                                       mm.vtk_progress_cb(s._reader))
	
        self._view_frame = None
        self.create_view_window()
	self.sync_config()
	
    def close(self):
        self._view_frame.Destroy()
	if hasattr(self, '_reader'):
	    del self._reader

    def get_input_descriptions(self):
	return ()
    
    def set_input(self, idx, input_stream):
	raise Exception
    
    def get_output_descriptions(self):
	return (self._reader.GetOutput().GetClassName(),)
    
    def get_output(self, idx):
	return self._reader.GetOutput()
    
    def sync_config(self):
        fn_text = XMLCTRL(self._view_frame, 'MV_ID_FILENAME')
        filename = self._reader.GetFileName()
        if filename == None:
            filename = ""
        fn_text.SetValue(filename)
	
    def apply_config(self):
        fn_text = XMLCTRL(self._view_frame, 'MV_ID_FILENAME')        
        self._reader.SetFileName(fn_text.GetValue())

    def execute_module(self):
        # get the vtkPolyDataReader to try and execute
	self._reader.Update()
        # tell the vtk log file window to poll the file; if the file has
        # changed, i.e. vtk has written some errors, the log window will
        # pop up
        self._module_manager.vtk_poll_error()

    def create_view_window(self):
        parent_window = self._module_manager.get_module_view_parent_window()

        self._view_frame = wxFrame(parent=parent_window, id=-1,
                                   title='vtk_plydta_rdr configuration')
        EVT_CLOSE(self._view_frame,
                  lambda e, s=self: s._view_frame.Show(false))

        # get out the panel resource that is constitutes this view
        res_path = os.path.join(self._module_manager.get_modules_xml_res_dir(),
                                'vtk_plydta_rdr.xrc')
        res = wxXmlResource(res_path)
        panel = res.LoadPanel(self._view_frame, 'PNL_VTK_PLYDTA_RDR_VIEW')

        # as per usual make one more top level sizer and add only the panel
        top_sizer = wxBoxSizer(wxVERTICAL)
        top_sizer.Add(panel, option=1, flag=wxEXPAND)

        # then make sure the frame will use the top_level sizer
        self._view_frame.SetAutoLayout(true)
        self._view_frame.SetSizer(top_sizer)
        # make the frame big enough to fit the sizer
        top_sizer.Fit(self._view_frame)
        # make sure the frame can't get smaller than the minimum sizer size
        top_sizer.SetSizeHints(self._view_frame)

        # bind events specific to this bitch
        EVT_BUTTON(self._view_frame, XMLID('MV_ID_BROWSE'), self.fn_browse_cb)
        EVT_CHOICE(self._view_frame, XMLID('MV_ID_VTK_OBJECT_CHOICE'),
                   self.vtk_object_choice_cb)
        EVT_BUTTON(self._view_frame, XMLID('MV_ID_VTK_PIPELINE'),
                   self.vtk_pipeline_cb)

        # bind events to the standard cancel, sync, apply, execute, ok buttons
        module_utils.bind_CSAEO(self, self._view_frame)
            
    def view(self, parent_window=None):
	# first make sure that our variables agree with the stuff that
        # we're configuring
	self.sync_config()
        self._view_frame.Show(true)
        
    def fn_browse_cb(self, event):
        path = self.fn_browse(self._view_frame,
                              "Choose a VTK polydata filename",
                              "VTK Polydata (*.vtk)|*.vtk|All files (*)|*")

        if path != None:
            fn_text = XMLCTRL(self._view_frame, 'MV_ID_FILENAME')
            fn_text.SetValue(path)

    def vtk_object_choice_cb(self, event):
        choice = XMLCTRL(self._view_frame,'MV_ID_VTK_OBJECT_CHOICE')
        if choice != None:
            if choice.GetStringSelection() == 'vtkPolyDataReader':
                self.vtk_object_configure(self._view_frame, None, self._reader)

    def vtk_pipeline_cb(self, event):
        # move this to module utils too, or to base...
        self.vtk_pipeline_configure(self._view_frame, None, (self._reader,))
	    
