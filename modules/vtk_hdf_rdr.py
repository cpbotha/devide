# $Id: vtk_hdf_rdr.py,v 1.14 2002/05/14 13:40:09 cpbotha Exp $

from module_base import \
     module_base, \
     module_mixin_vtk_pipeline_config, \
     module_mixin_fo_dialog
from wxPython.wx import *
from wxPython.xrc import *
import os
import vtkpython
import vtkcpbothapython
import module_utils

class vtk_hdf_rdr(module_base,
                  module_mixin_vtk_pipeline_config,
                  module_mixin_fo_dialog):
    """dscas3 module for reading dscas HDF datasets.

    The platform makes use of HDF SDS with a custom spacing attribute.
    """
    
    def __init__(self, module_manager):
        # call the base class __init__ (atm it just stores module_manager)
        module_base.__init__(self, module_manager)
	self._reader = vtkcpbothapython.vtkHDFVolumeReader()

        # declare this var here out of good habit
        self._view_frame = None
        # go on, create that view window
        self.create_view_window(module_manager.get_module_view_parent_window())
        # make sure it's reflecting what it should
	self.sync_config()
    
    def close(self):
        self._view_frame.Destroy()
	if hasattr(self, 'reader'):
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
        fn = self._reader.GetFileName()
        if fn == None: fn = ""
        fn_text.SetValue(fn)
	
    def apply_config(self):
        fn_text = XMLCTRL(self._view_frame, 'MV_ID_FILENAME')
        self._reader.SetFileName(fn_text.GetValue())
	
    def execute_module(self):
	self._reader.Update()

    def create_view_window(self, parent_window=None):
        """Create configuration/view window.

        This method sets up the config window and immediately hides it.  When
        the user wants to view/config, the window is simply de-iconised.
        """

        # first create the fram and make sure that when the user closes it
        # it only hides itself, tee hee
        self._view_frame = wxFrame(parent=parent_window, id=-1,
                                   title='vtk_hdf_rdr configuration')
        EVT_CLOSE(self._view_frame,
                  lambda e, s=self: s._view_frame.Show(false))

        # get out the panel resource that is constitutes this view
        res_path = os.path.join(self._module_manager.get_modules_xml_res_dir(),
                                'vtk_hdf_rdr.xrc')
        res = wxXmlResource(res_path)
        panel = res.LoadPanel(self._view_frame, 'PNL_VTK_HDF_RDR_VIEW')

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
        path = self.fn_browse(self._view_frame, "Choose an HDF filename",
                              "HDF files (*.hdf)|*.hdf|All files (*)|*")

        if path != None:
            fn_text = XMLCTRL(self._view_frame, 'MV_ID_FILENAME')
            fn_text.SetValue(path)

    def vtk_object_choice_cb(self, event):
        choice = XMLCTRL(self._view_frame,'MV_ID_VTK_OBJECT_CHOICE')
        if choice != None:
            if choice.GetStringSelection() == 'vtkHDFVolumeReader':
                self.vtk_object_configure(self._view_frame, None, self._reader)

    def vtk_pipeline_cb(self, event):
        # move this to module utils too, or to base...
        self.vtk_pipeline_configure(self._view_frame, None, (self._reader,))

        
        
	
    
