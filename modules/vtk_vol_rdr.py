from module_base import \
     module_base, \
     module_mixin_vtk_pipeline_config, \
     module_mixin_fo_dialog
from wxPython.wx import *
from wxPython.xrc import *
import vtk
import gen_utils
import module_constants
import module_utils
import os

class vtk_vol_rdr(module_base,
                  module_mixin_vtk_pipeline_config,
                  module_mixin_fo_dialog):

    def __init__(self, module_manager):
        # call the base class __init__ (atm it just stores module_manager)
        module_base.__init__(self, module_manager)

	self._reader = vtk.vtkImageReader()
        # with this call we make sure that the vtkImageReader doesn't try
        # to calculate header size by itself
        self._reader.SetHeaderSize(0)

        # declare this var here out of good habit
        self._view_frame = None
        # go on, create that view window
        self.create_view_window(module_manager.get_module_view_parent_window())
        # make sure it's reflecting what it should
	self.sync_config()
    
    def close(self):
        # destroy the frame, which should take care of ALL its children
        self._view_frame.Destroy()
        # make sure we have no references to this guy, so it can disappear
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
        filename = self._reader.GetFileName()
        if filename == None:
            filename = ""
        fn_text = XMLCTRL(self._view_frame, 'MV_ID_FILENAME')            
        fn_text.SetValue(filename)

        hs_text = XMLCTRL(self._view_frame, 'MV_ID_HEADER_SIZE')
        hs_text.SetValue(str(self._reader.GetHeaderSize()))

        st = self._reader.GetDataScalarType()
        # now index st into dict module_constants.vtk_types
        if st in module_constants.vtk_types.values():
            v_idx = module_constants.vtk_types.values().index(st)
            # get the key
            v_key = module_constants.vtk_types.keys()[v_idx]
            dt_choice = XMLCTRL(self._view_frame, 'MV_ID_DATA_TYPE_CHOICE')
            dt_choice.SetStringSelection(v_key)

        # 0 is big, 1 is little
        e_cb = XMLCTRL(self._view_frame, 'MV_ID_ENDIANNESS')
        if self._reader.GetDataByteOrder() == 0:
            e_cb.SetValue(true)
        else:
            e_cb.SetValue(false)

        extent = self._reader.GetDataExtent()
        ext_text = XMLCTRL(self._view_frame, 'MV_ID_EXTENT')
        ext_text.SetValue(str(extent))

        spacing = self._reader.GetDataSpacing()
        spacing_text = XMLCTRL(self._view_frame, 'MV_ID_SPACING')
        spacing_text.SetValue(str(spacing))
	
    def apply_config(self):
        try:
            fn_text = XMLCTRL(self._view_frame, 'MV_ID_FILENAME')        
            self._reader.SetFileName(fn_text.GetValue())

            hs_text = XMLCTRL(self._view_frame, 'MV_ID_HEADER_SIZE')
            self._reader.SetHeaderSize(int(hs_text.GetValue()))

            dt_choice = XMLCTRL(self._view_frame, 'MV_ID_DATA_TYPE_CHOICE')
            dtype = module_constants.vtk_types[dt_choice.GetStringSelection()]
            self._reader.SetDataScalarType(dtype)

            e_cb = XMLCTRL(self._view_frame, 'MV_ID_ENDIANNESS')
            if e_cb.GetValue():
                self._reader.SetDataByteOrderToBigEndian()
            else:
                self._reader.SetDataByteOrderToLittleEndian()
            
            ext_text = XMLCTRL(self._view_frame, 'MV_ID_EXTENT')
            eval('self._reader.SetDataExtent(%s)' % (ext_text.GetValue()))

            spacing_text = XMLCTRL(self._view_frame, 'MV_ID_SPACING')
            eval('self._reader.SetDataSpacing(%s)' %
                 (spacing_text.GetValue()))
        except Exception, e:
            gen_utils.log_error(str(e))
            
        
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
                                   title='vtk_vol_rdr configuration')
        EVT_CLOSE(self._view_frame,
                  lambda e, s=self: s._view_frame.Show(false))

        # get out the panel resource that is constitutes this view
        res_path = os.path.join(self._module_manager.get_modules_xml_res_dir(),
                                'vtk_vol_rdr.xrc')
        res = wxXmlResource(res_path)
        panel = res.LoadPanel(self._view_frame, 'PNL_VTK_VOL_RDR_VIEW')

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
        path = self.fn_browse(self._view_frame, "Choose a volume filename",
                              "All files (*)|*")

        if path != None:
            fn_text = XMLCTRL(self._view_frame, 'MV_ID_FILENAME')
            fn_text.SetValue(path)

    def vtk_object_choice_cb(self, event):
        choice = XMLCTRL(self._view_frame,'MV_ID_VTK_OBJECT_CHOICE')
        if choice != None:
            if choice.GetStringSelection() == 'vtkImageReader':
                self.vtk_object_configure(self._view_frame, None, self._reader)

    def vtk_pipeline_cb(self, event):
        # move this to module utils too, or to base...
        self.vtk_pipeline_configure(self._view_frame, None, (self._reader,))
