# $Id: vtk_slice_vwr.py,v 1.58 2002/09/03 15:55:24 cpbotha Exp $

# TODO: vtkTextureMapToPlane, like thingy...

from gen_utils import log_error
from module_base import module_base, module_mixin_vtk_pipeline_config
import vtk
import vtkcpbothapython
from wxPython.wx import *
from wxPython.xrc import *
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor
import operator

# wxGTK 2.3.2.1 bugs with mouse capture (BADLY), so we disable this
try:
    WX_USE_X_CAPTURE
except NameError:
    if wxPlatform == '__WXMSW__':
        WX_USE_X_CAPTURE = 1
    else:
        WX_USE_X_CAPTURE = 0

class vtk_slice_vwr(module_base,
                    module_mixin_vtk_pipeline_config):
    
    """Slicing, dicing slice viewing class.

    This class is used as a dscas3 module.  Given vtkImageData-like input data,
    it will show 3 slices and 3 planes in a 3d scene.  PolyData objects can
    also be added.  One can interact with the 3d slices to change the slice
    orientation and position.
    """

    def __init__(self, module_manager):
        # call base constructor
        module_base.__init__(self, module_manager)
        self._num_inputs = 5
        # use list comprehension to create list keeping track of inputs
        self._inputs = [{'Connected' : None, 'vtkActor' : None}
                       for i in range(self._num_inputs)]
        # then the window containing the renderwindows
        self._view_frame = None
        # we have a single RenderWindowInteractor
        self._rwi = None
        self._ipws = []
        # list of current cursors, one cursor for each ipw
        self._current_cursors = []
        # the renderers corresponding to the render windows
        self._renderer = None

        # list of selected points (we can make this grow or be overwritten)
        self._sel_points = []

        self._outline_source = vtk.vtkOutlineSource()
        om = vtk.vtkPolyDataMapper()
        om.SetInput(self._outline_source.GetOutput())
        self._outline_actor = vtk.vtkActor()
        self._outline_actor.SetMapper(om)
        self._cube_axes_actor2d = vtk.vtkCubeAxesActor2D()

        self._left_mouse_button = 0

        # make the list of imageplanewidgets
        self._ipws = [vtk.vtkImagePlaneWidget() for i in range(3)]
        self._current_cursors = [[0,0,0,0] for i in self._ipws]
        
        # set the whole UI up!
        self._create_window()
        
    def close(self):
        for idx in range(self._num_inputs):
            self.set_input(idx, None)
        
        del self._outline_source
        del self._outline_actor
        del self._cube_axes_actor2d
        
        if hasattr(self, '_ipws'):
            del self._ipws
        if hasattr(self, '_renderer'):
            del self._renderer
        if hasattr(self, '_rwi'):
            del self._rwi
        if hasattr(self,'_view_frame'):
            self._view_frame.Destroy()
            del self._view_frame

#################################################################
# module API methods
#################################################################

    def get_input_descriptions(self):
        # concatenate it num_inputs times (but these are shallow copies!)
        return self._num_inputs * \
               ('vtkStructuredPoints|vtkImageData|vtkPolyData',)

    def set_input(self, idx, input_stream):
        if input_stream == None:

            if self._inputs[idx]['Connected'] == 'vtkPolyData':
                self._inputs[idx]['Connected'] = None
                if self._inputs[idx]['vtkActor'] != None:
                    self._renderer.RemoveActor(self._inputs[idx]['vtkActor'])
                    self._inputs[idx]['vtkActor'] = None

            elif self._inputs[idx]['Connected'] == 'vtkImageData':
                self._inputs[idx]['Connected'] = None

                # by definition, we only have one set of vtkImagePlaneWidgets
                # let's disconnect them
                for ipw in self._ipws:
                    ipw.SetInput(None)
                    ipw.Off()
                    ipw.SetInteractor(None)

                self._renderer.RemoveActor(self._outline_actor)
                self._renderer.RemoveActor(self._cube_axes_actor2d)

        elif hasattr(input_stream, 'GetClassName') and \
             callable(input_stream.GetClassName):

            if input_stream.GetClassName() == 'vtkPolyData':
               
                mapper = vtk.vtkPolyDataMapper()
                mapper.SetInput(input_stream)
                self._inputs[idx]['vtkActor'] = vtk.vtkActor()
                self._inputs[idx]['vtkActor'].SetMapper(mapper)
                self._renderer.AddActor(self._inputs[idx]['vtkActor'])
                self._inputs[idx]['Connected'] = 'vtkPolyData'
                self._renderer.ResetCamera()                
                self._rwi.Render()
                
            elif input_stream.IsA('vtkImageData'):

                # if we already have an ImageData input, we can't take anymore
                for input in self._inputs:
                    if input['Connected'] == 'vtkImageData':
                        raise TypeError, "You have tried to add volume data " \
                              "the slice viewer which already has a " \
                              "connected volume data set.  Disconnect the " \
                              "old dataset first."

                # make sure it's current
                input_stream.Update()

                for ipw in self._ipws:
                    ipw.SetInput(input_stream)

                self._renderer.AddActor(self._outline_actor)
                self._outline_actor.PickableOff()
                self._renderer.AddActor(self._cube_axes_actor2d)
                self._cube_axes_actor2d.PickableOff()

                self._reset()

                self._rwi.Render()
                self._inputs[idx]['Connected'] = 'vtkImageData'

            else:
                raise TypeError, "Wrong input type!"

        # make sure we catch any errors!
        self._module_manager.vtk_poll_error()

        
    def get_output_descriptions(self):
        # return empty tuple
        return ()
        
    def get_output(self, idx):
        raise Exception

    def view(self):
        self._view_frame.Show(true)

#################################################################
# utility methods
#################################################################

    def _create_ipw_panel(self, parent, i):

        ipw = self._ipws[i]
        
        panel = wxPanel(parent, -1)

        eid = wxNewId()
        # this is just too useful, embedding variables in existing
        # instances.
        panel.enabled_cbox = wxCheckBox(panel, eid, 'Enabled')
        panel.enabled_cbox.SetValue(true)

        def _eb_cb(event):
            if ipw.GetInput():
                if panel.enabled_cbox.GetValue():
                    ipw.On()
                else:
                    ipw.Off()
        
        EVT_CHECKBOX(panel, eid, _eb_cb)

        # now we have to make a space for the latest coord
        st = wxStaticText(panel, -1, "Cursor at")
        panel.cursor_text = wxTextCtrl(panel, -1)
        sid = wxNewId()
        sb = wxButton(panel, sid, "Store")

        EVT_BUTTON(panel, sid, lambda e, i=i: self._store_cursor_cb(i))
        
        hz = wxBoxSizer(wxHORIZONTAL)
        hz.Add(st, 0, wxLEFT|wxRIGHT|wxALIGN_CENTER_VERTICAL, 2)
        hz.Add(panel.cursor_text, option=1,
               flag=wxEXPAND|wxALIGN_CENTER_VERTICAL)
        hz.Add(sb)

        tls = wxBoxSizer(wxVERTICAL)
        tls.Add(panel.enabled_cbox, flag=wxALL, border=5)
        tls.Add(hz, option=0, flag=wxEXPAND|wxALL, border=5)

        #tls.Fit(panel)
        panel.SetAutoLayout(true)
        panel.SetSizer(tls)
        
        return panel

    def _create_window(self):
        # create main frame, make sure that when it's closed, it merely hides
        parent_window = self._module_manager.get_module_view_parent_window()
        self._view_frame = wxFrame(parent=parent_window, id=-1,
                                   title='slice viewer')
        EVT_CLOSE(self._view_frame,
                  lambda e, s=self: s._view_frame.Show(false))

        # panel inside the frame
        panel = wxPanel(self._view_frame, id=-1)

        # then setup the renderwindow
        # -----------------------------------------------------------------
        self._rwi = wxVTKRenderWindowInteractor(panel, -1, size=(640,480))
        self._renderer = vtk.vtkRenderer()
        self._renderer.SetBackground(0.5,0.5,0.5)
        self._rwi.GetRenderWindow().AddRenderer(self._renderer)
        

        # then the selected point list control
        # -----------------------------------------------------------------
        self._spoint_listctrl = wxListCtrl(panel, -1, size=(280,100),
                                           style=wxLC_REPORT|wxSUNKEN_BORDER|
                                           wxLC_HRULES|wxLC_VRULES)
        self._spoint_listctrl.InsertColumn(0, 'Position')
        self._spoint_listctrl.SetColumnWidth(0, 180)
        self._spoint_listctrl.InsertColumn(2, 'Value')
        self._spoint_listctrl.SetColumnWidth(2, 100)                
        #self._spoint_listctrl.InsertStringItem(0, 'yaa')
        #self._spoint_listctrl.InsertStringItem(1, 'yaa2')        

        
        # the button control panel
        # -----------------------------------------------------------------
        pcid = wxNewId()
        pcb = wxButton(panel, pcid, 'Pipeline')
        EVT_BUTTON(panel, pcid, lambda e, pw=self._view_frame, s=self,
                   rw=self._rwi.GetRenderWindow():
                   s.vtk_pipeline_configure(pw, rw))

        rid = wxNewId()
        rb = wxButton(panel, rid, 'Reset')
        EVT_BUTTON(panel, rid, lambda e, s=self: s._reset())


        # slices notebook
        # -----------------------------------------------------------------

        nb_id = wxNewId()
        self._acs_nb = wxNotebook(panel, nb_id)
        # by this time the _ipws must exist!
        pnames = ["Axial", "Coronal", "Sagittal"]
        for i in range(len(self._ipws)):
            # create and populate panel
            spanel = self._create_ipw_panel(self._acs_nb, i)
            self._acs_nb.AddPage(spanel, pnames[i])
            # now make callback for the ipw
            self._ipws[i].AddObserver('StartInteractionEvent',
                                      lambda e, o, i=i:
                                      self._ipw_start_interaction_cb(i))
            self._ipws[i].AddObserver('InteractionEvent',
                                      lambda e, o, i=i:
                                      self._ipw_interaction_cb(i))

        EVT_NOTEBOOK_PAGE_CHANGED(panel, nb_id, self._acs_nb_page_changed_cb)


        # all the sizers
        # -----------------------------------------------------------------
        
        button_sizer = wxBoxSizer(wxHORIZONTAL)
        button_sizer.Add(pcb)
        button_sizer.Add(rb)

        # we need a special sizer that determines the largest sizer
        # on all of the notebook's pages
        nbs = wxNotebookSizer(self._acs_nb)

        # this sizer will contain the button_sizer and the notebook
        button_nb_sizer = wxBoxSizer(wxVERTICAL)
        button_nb_sizer.Add(button_sizer)
        button_nb_sizer.Add(nbs, option=1, flag=wxEXPAND)

        # this sizer contains the selected points list, buttons and notebook
        bottom_sizer = wxBoxSizer(wxHORIZONTAL)
        bottom_sizer.Add(self._spoint_listctrl, option=1, flag=wxEXPAND)
        bottom_sizer.Add(button_nb_sizer, option=1, flag=wxEXPAND)

        # top level sizer
        tl_sizer = wxBoxSizer(wxVERTICAL)
        tl_sizer.Add(self._rwi, option=1, flag=wxEXPAND)
        tl_sizer.Add(bottom_sizer, flag=wxEXPAND)

        panel.SetAutoLayout(true)
        panel.SetSizer(tl_sizer)
        tl_sizer.Fit(self._view_frame)
        #tl_sizer.SetSizeHints(self._view_frame)

        self._view_frame.Show(true)

    def _reset(self):
        """Arrange everything for a single overlay in a single ortho view.

        This method is to be called AFTER the pertinent VTK pipeline has been
        setup.  This is here, because one often connects modules together
        before source modules have been configured, i.e. the success of this
        method is dependent on whether the source modules have been configged.
        HOWEVER: it won't die if it hasn't, just complain.

        It will configure all 3d widgets and textures and thingies, but it
        won't CREATE anything.
        """

        # if we don't have any _ipws, it means we haven't been given data
        # yet, so let's bail
        if len(self._ipws) <= 0:
            return

        input_data = self._ipws[0].GetInput()

        # we might have ipws, but no input_data, in which we can't do anything
        # either, so we bail
        if input_data is None:
            return

        # make sure this is all nicely up to date
        input_data.Update()

        # set up helper actors
        self._outline_source.SetBounds(input_data.GetBounds())
        self._cube_axes_actor2d.SetBounds(input_data.GetBounds())
        self._cube_axes_actor2d.SetCamera(self._renderer.GetActiveCamera())

        # calculate default window/level once
        (dmin,dmax) = input_data.GetScalarRange()
        iwindow = (dmax - dmin) / 2
        ilevel = dmin + iwindow

        # colours of imageplanes; we will use these as keys
        ipw_cols = [(1,0,0), (0,1,0), (0,0,1)]

        idx = 2
        for ipw in self._ipws:
            ipw.DisplayTextOn()
            ipw.SetInteractor(self._rwi)
            ipw.SetPlaneOrientation(idx)
            idx -= 1
            ipw.SetSliceIndex(0)
            #ipw.SetPicker(some_same_picker)
            #ipw.SetKeyPressActivationValue('x')
            ipw.GetPlaneProperty().SetColor(ipw_cols[idx])

            # see if the creator of the input_data can tell
            # us something about Window/Level
            input_data_source = ipw.GetInput().GetSource()
            print input_data_source.__class__

            if hasattr(input_data_source, 'GetWindowCenter') and \
               callable(input_data_source.GetWindowCenter):
                level = input_data_source.GetWindowCenter()
                print "Retrieved level of %f" % level
            else:
                level = ilevel

            if hasattr(input_data_source, 'GetWindowWidth') and \
               callable(input_data_source.GetWindowWidth):
                window = input_data_source.GetWindowWidth()
                print "Retrieved window of %f" % window
            else:
                window = iwindow

            lut = vtk.vtkWindowLevelLookupTable()
            lut.SetWindow(window)
            lut.SetLevel(level)
            lut.Build()
            ipw.SetLookupTable(lut)
            ipw.On()

        self._renderer.ResetCamera()

        # whee, thaaaar she goes.
        self._rwi.Render()

        # now also make sure that the notebook with slice config is updated
        self._acs_nb_page_changed_cb(None)

    def _store_cursor(self, cursor):
        
        input_data = self._ipws[0].GetInput()
        ispacing = input_data.GetSpacing()
        iorigin = input_data.GetSpacing()
        # calculate real coords
        coords = map(operator.add, iorigin,
                     map(operator.mul, ispacing, cursor[0:3]))
        
        # setup a pipeline to indicate position of selected point
        axes = vtk.vtkAxes()
        axes.SetOrigin(coords)
        axes.SetScaleFactor(30.0)
        axes.SymmetricOn()

        axes_tf = vtk.vtkTubeFilter()
        axes_tf.SetInput(axes.GetOutput())
        bounds = input_data.GetBounds()
        axes_tf.SetRadius((bounds[1] - bounds[0]) / 100.0)
        axes_tf.SetNumberOfSides(6)

        axes_mapper = vtk.vtkPolyDataMapper()
        axes_mapper.SetInput(axes_tf.GetOutput())
        
        axes_actor = vtk.vtkActor()
        axes_actor.SetMapper(axes_mapper)
        axes_actor.GetProperty().BackfaceCullingOff()
        self._renderer.AddActor(axes_actor)
        
        # store the cursor (discrete coords) the coords and the actor
        self._sel_points.append({'cursor' : cursor, 'coords' : coords,
                                 'actor' : axes_actor})

        def ca_pe_cb(actor, evtname):

            # we have to search for "actor" in the _self_points :(
            actors = map(lambda i: i['actor'], self._sel_points)
            if actor in actors:
                # FIXME: continue here
                pass
                #self._spoint_listctrl(actors.index(actor))
                
        axes_actor.AddObserver('PickEvent', ca_pe_cb)
        
        # *sniff* *sob* It's unreadable, but why's it so pretty?
        # this just formats the real point
        pos_str = "%s, %s, %s" % tuple(cursor[0:3])
        idx = self._spoint_listctrl.InsertStringItem(0, pos_str)
        # this adds a line to our list of points (for later manip)
        self._spoint_listctrl.SetStringItem(idx, 1, str(cursor[3]))

        self._rwi.Render()
        
        
#################################################################
# callbacks
#################################################################

    def _acs_nb_page_changed_cb(self, event):
        cur_panel = self._acs_nb.GetPage(self._acs_nb.GetSelection())
        if self._ipws[self._acs_nb.GetSelection()].GetEnabled():
            cur_panel.enabled_cbox.SetValue(true)
        else:
            cur_panel.enabled_cbox.SetValue(false)

    def _ipw_start_interaction_cb(self, i):
        self._acs_nb.SetSelection(i)
        self._ipw_interaction_cb(i)

    def _ipw_interaction_cb(self, i):
        cd = 4 * [0.0]
        if self._ipws[i].GetCursorData(cd):
            cur_panel = self._acs_nb.GetPage(self._acs_nb.GetSelection())
            self._current_cursors[i] = cd
            cstring = str(cd[0:3]) + " = " + str(cd[3])
            cur_panel.cursor_text.SetValue(cstring)

    def _rw_ortho_pick_cb(self, wxvtkrwi):
        (cx,cy) = wxvtkrwi.GetEventPosition()
        r_idx = self._rwis.index(wxvtkrwi)

        # there has to be data in this pipeline before we can go on
        if len(self._ortho_pipes[r_idx - 1]):
        
            # instantiate WorldPointPicker and use it to get the World Point
            # that we've selected
            wpp = vtk.vtkWorldPointPicker()
            wpp.Pick(cx,cy,0,self._renderers[r_idx])
            (ppx,ppy,ppz) = wpp.GetPickPosition()
            # ppz will be zero too

            # now check that it's within bounds of the sliced data
            reslice = self._ortho_pipes[r_idx - 1][0]['vtkImageReslice']
            rbounds = reslice.GetOutput().GetBounds()

            if ppx >= rbounds[0] and ppx <= rbounds[1] and \
               ppy >= rbounds[2] and ppy <= rbounds[3]:

                # this is just the way that the ResliceAxes are constructed
                # here we do: inpoint = ra * pp
                ra = reslice.GetResliceAxes()
                inpoint = ra.MultiplyPoint((ppx,ppy,ppz,1))

                input_bounds = reslice.GetInput().GetBounds()
                
                # now put this point in the applicable list
                # check that the point is in the volume
                # later we'll have a multi-point mode which is when this
                # "1" conditional will be used
                if 1 and \
                   inpoint[2] >= input_bounds[4] and \
                   inpoint[2] <= input_bounds[5]:

                    self._add_sel_point(inpoint[0:3], r_idx - 1)

                    #self._ortho_huds[r_idx - 1]['vtkAxes'].SetOrigin(ppx,ppy,
                    #                                                 0.5)
                    #self._ortho_huds[r_idx - 1]['axes_actor'].VisibilityOn()

                    self._rwis[r_idx].Render()
    
    def _rw_slice_cb(self, wxvtkrwi):
        delta = wxvtkrwi.GetEventPosition()[1] - \
                wxvtkrwi.GetLastEventPosition()[1]

        r_idx = self._rwis.index(wxvtkrwi)

        if len(self._ortho_pipes[r_idx - 1]):
            # we make use of the spacing of the first layer, so there
            reslice = self._ortho_pipes[r_idx - 1][0]['vtkImageReslice']
            reslice.UpdateInformation()

            input_spacing = reslice.GetInput().GetSpacing()
            rai = vtk.vtkMatrix4x4()
            vtk.vtkMatrix4x4.Invert(reslice.GetResliceAxes(), rai)
            output_spacing = rai.MultiplyPoint(input_spacing + (0.0,))

            # modify the underlying polydatasource of the planewidget
            ps = self._pws[r_idx - 1].GetPolyDataSource()
            ps.Push(delta * output_spacing[2])
            self._pws[r_idx - 1].UpdatePlacement()

            # then call the pw callback (tee hee)
            self._pw_cb(self._pws[r_idx - 1], r_idx - 1)
            
            # render the 3d viewer
            self._rwis[0].Render()

    def _rw_windowlevel_cb(self, wxvtkrwi):
        deltax = wxvtkrwi.GetEventPosition()[0] - \
                 wxvtkrwi.GetLastEventPosition()[0]     
        
        deltay = wxvtkrwi.GetEventPosition()[1] - \
                 wxvtkrwi.GetLastEventPosition()[1]

        ortho_idx = self._rwis.index(wxvtkrwi) - 1

        for layer_pl in self._ortho_pipes[ortho_idx]:
            lut = layer_pl['vtkLookupTable']
            lut.SetLevel(lut.GetLevel() + deltay * 5.0)
            lut.SetWindow(lut.GetWindow() + deltax * 5.0)
            lut.Build()

        wxvtkrwi.GetRenderWindow().Render()
        self._rwis[0].GetRenderWindow().Render()

    def _store_cursor_cb(self, i):
        self._store_cursor(self._current_cursors[i])
        
