# slice3d_vwr.py copyright (c) 2002 Charl P. Botha <cpbotha@ieee.org>
# $Id: slice3d_vwr.py,v 1.14 2003/02/12 00:24:41 cpbotha Exp $
# next-generation of the slicing and dicing dscas3 module

# TODO:
# * add 2 orthogonal views again
# * 

from gen_utils import log_error
from moduleBase import moduleBase
from moduleMixins import vtkPipelineConfigModuleMixin
import vtk
from wxPython.wx import *
from wxPython.grid import *
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

class slice3d_vwr(moduleBase,
                  vtkPipelineConfigModuleMixin):
    
    """Slicing, dicing slice viewing class.

    This class is used as a dscas3 module.  Given vtkImageData-like input data,
    it will show 3 slices and 3 planes in a 3d scene.  PolyData objects can
    also be added.  One can interact with the 3d slices to change the slice
    orientation and position.
    """

    def __init__(self, moduleManager):
        # call base constructor
        moduleBase.__init__(self, moduleManager)
        self._numDataInputs = 5
        # use list comprehension to create list keeping track of inputs
        self._inputs = [{'Connected' : None, 'observerID' : -1,
                         'vtkActor' : None}
                       for i in range(self._numDataInputs)]
        # then the window containing the renderwindows
        self._view_frame = None
        # the imageplanewidgets
        self._ipws = []
        self._overlay_ipws = []
        # list of current cursors, one cursor for each ipw
        self._current_cursors = []
        # the renderers corresponding to the render windows
        self._threedRenderer = None
        self._ortho1Renderer = None
        self._ortho2Renderer = None

        # list of selected points (we can make this grow or be overwritten)
        self._sel_points = []
        # this will be passed on as input to the next component
        self._vtk_points = vtk.vtkPoints()
        # this is an extra output with text descriptions for each points
        self._vtk_points_names = []

        self._outline_source = vtk.vtkOutlineSource()
        om = vtk.vtkPolyDataMapper()
        om.SetInput(self._outline_source.GetOutput())
        self._outline_actor = vtk.vtkActor()
        self._outline_actor.SetMapper(om)
        self._cube_axes_actor2d = vtk.vtkCubeAxesActor2D()

        # use box widget for VOI selection
        self._voi_widget = vtk.vtkBoxWidget()
        # we want to keep it aligned with the cubic volume, thanks
        self._voi_widget.SetRotationEnabled(0)
        self._voi_widget.AddObserver('InteractionEvent',
                                     self.voiWidgetInteractionCallback)
        self._voi_widget.AddObserver('EndInteractionEvent',
                                     self.voiWidgetEndInteractionCallback)

        # also create the VTK construct for actually extracting VOI from data
        self._extractVOI = vtk.vtkExtractVOI()
        self._currentVOI = 6 * [0]

        self._left_mouse_button = 0

        # make the list of imageplanewidgets
        self._ipws = [vtk.vtkImagePlaneWidget() for i in range(3)]
        # set the same picker for each vtkIPW
        picker = vtk.vtkCellPicker()
        for ipw in self._ipws:
            ipw.SetPicker(picker)
        
        self._current_cursors = [[0,0,0,0] for i in self._ipws]
        
        # set the whole UI up!
        self._create_window()

#################################################################
# module API methods
#################################################################
        
    def close(self):
        # this is standard behaviour in the close method:
        # call set_input(idx, None) for all inputs
        for idx in range(self._numDataInputs):
            self.setInput(idx, None)
        
        # unbind everything that we bound in our __init__
        del self._outline_source
        del self._outline_actor
        del self._cube_axes_actor2d
        del self._voi_widget
        del self._extractVOI
        
	del self._ipws

        # take care of all our bindings to renderers
        del self._threedRenderer
        del self._ortho1Renderer
        del self._ortho2Renderer

        # the remaining bit of logic is quite crucial:
        # we can't explicitly Destroy() the frame, as the RWI that it contains
        # will only disappear when it's reference count reaches 0, and we
        # can't really force that to happen either.  If you DO Destroy() the
        # frame before the RW destructs, it will cause the application to
        # crash because the RW assumes a valid WindowId in its dtor
        #
        # we have two solutions:
        # 1. call a WindowRemap on the RenderWindows so that they reparent
        #    themselves to newly created windowids
        # 2. attach event handlers to the RenderWindow DeleteEvent and
        #    destroy the containing frame from there
        #
        # method 2 doesn't alway work, so we use WindowRemap

	# hide it so long
	#self._view_frame.Show(0)

        self._view_frame.threedRWI.GetRenderWindow().SetSize(10,10)
        self._view_frame.threedRWI.GetRenderWindow().WindowRemap()        
        self._view_frame.ortho1RWI.GetRenderWindow().SetSize(10,10)
        self._view_frame.ortho1RWI.GetRenderWindow().WindowRemap()        
        self._view_frame.ortho2RWI.GetRenderWindow().SetSize(10,10)
        self._view_frame.ortho2RWI.GetRenderWindow().WindowRemap()        
        
        # all the RenderWindow()s are now reparented, so we can destroy
        # the containing frame
        self._view_frame.Destroy()
	# unbind the _view_frame binding
	del self._view_frame
	
    def getInputDescriptions(self):
        # concatenate it num_inputs times (but these are shallow copies!)
        return self._numDataInputs * \
               ('vtkStructuredPoints|vtkImageData|vtkPolyData',)

    def setInput(self, idx, input_stream):
        if input_stream == None:

            if self._inputs[idx]['Connected'] == 'vtkPolyData':
                self._inputs[idx]['Connected'] = None
                actor = self._inputs[idx]['vtkActor']
                if actor != None:
                    if self._inputs[idx]['observerID'] >= 0:
                        # remove the observer (if we had one)
                        actor.GetMapper().GetInput().RemoveObserver(
                            self._inputs[idx]['observerID'])
                        self._inputs[idx]['observerID'] = -1

                    self._threedRenderer.RemoveActor(self._inputs[idx][
                        'vtkActor'])
                    self._inputs[idx]['vtkActor'] = None

            elif self._inputs[idx]['Connected'] == 'vtkImageData':
                self._inputs[idx]['Connected'] = None

                # remove our observer
                if self._inputs[idx]['observerID'] >= 0:
                    self._ipws[0].GetInput().RemoveObserver(
                        self._inputs[idx]['observerID'])
                    self._inputs[idx]['observerID'] = -1
                
                # by definition, we only have one set of vtkImagePlaneWidgets
                # let's disconnect them
                for ipw in self._ipws:
                    ipw.Off()                    
                    ipw.SetInput(None)
                    ipw.SetInteractor(None)

                self._threedRenderer.RemoveActor(self._outline_actor)
                self._threedRenderer.RemoveActor(self._cube_axes_actor2d)

                # deactivate VOI widget as far as possible
                self._voi_widget.SetInput(None)
                self._voi_widget.Off()
                self._voi_widget.SetInteractor(None)

                # and stop vtkExtractVOI from extracting more VOIs
                # we have to disconnect this, else the input data will
                # live on...
                self._extractVOI.SetInput(None)

        elif hasattr(input_stream, 'GetClassName') and \
             callable(input_stream.GetClassName):

            if input_stream.GetClassName() == 'vtkPolyData':
               
                mapper = vtk.vtkPolyDataMapper()
                mapper.SetInput(input_stream)
                self._inputs[idx]['vtkActor'] = vtk.vtkActor()
                self._inputs[idx]['vtkActor'].SetMapper(mapper)
                self._threedRenderer.AddActor(self._inputs[idx]['vtkActor'])
                self._inputs[idx]['Connected'] = 'vtkPolyData'
                self._threedRenderer.ResetCamera()
                self._view_frame.threedRWI.Render()

                # connect an event handler to the data
                oid = input_stream.AddObserver('ModifiedEvent',
                                               self.inputModifiedCallback)
                self._inputs[idx]['observerID'] = oid
                
                
            elif input_stream.IsA('vtkImageData'):

                # if we already have an ImageData input, we can't take anymore
                for input in self._inputs:
                    if input['Connected'] == 'vtkImageData':

                        # this means we might be getting on overlay
                        # first check that we don't already have an overlay
                        if self._overlay_ipws:
                            raise TypeError, \
                                  "This slice viewer already has an overlay. "\
                                  "You can't add another."

                        # check the overlay for size and spacing
                        input_stream.Update()

                        main_input = self._ipws[0].GetInput()

                        if input_stream.GetExtent() == \
                               main_input.GetExtent() and \
                               input_stream.GetSpacing() == \
                               main_input.GetSpacing():
                            
                            # add a set of overlays
                            self._overlay_ipws = [vtk.vtkImagePlaneWidget()
                                                  for i in range(3)]
                            
                                
                            
                            
                        else:
                            raise TypeError, \
                                  "You have tried to add volume data to " \
                                  "the slice viewer that already has a " \
                                  "connected volume data set.  Disconnect " \
                                  "the old dataset first or make sure that "\
                                  "the new dataset has the same dimensions "\
                                  "so that it can be used as overlay."

                # make sure it's current
                input_stream.Update()

                for ipw in self._ipws:
                    ipw.SetInput(input_stream)

                self._extractVOI.SetInput(input_stream)

                # add outline actor and cube axes actor to renderer
                self._threedRenderer.AddActor(self._outline_actor)
                self._outline_actor.PickableOff()
                self._threedRenderer.AddActor(self._cube_axes_actor2d)
                self._cube_axes_actor2d.PickableOff()

                # connect an event handler to the data
                oid = input_stream.AddObserver('ModifiedEvent',
                                               self.inputModifiedCallback)
                self._inputs[idx]['observerID'] = oid
                

                self._reset()

                self._view_frame.threedRWI.Render()
                self._inputs[idx]['Connected'] = 'vtkImageData'

            else:
                raise TypeError, "Wrong input type!"

        # make sure we catch any errors!
        self._moduleManager.vtk_poll_error()

        
    def getOutputDescriptions(self):
        return ('Selected points (vtkPoints)', 'Selected points names (list)',
                'Volume of Interest (vtkStructuredPoints)')
        
    def getOutput(self, idx):
        if idx == 0:
            return self._vtk_points
        elif idx == 1:
            return self._vtk_points_names
        else:
            return self._extractVOI.GetOutput()

    def view(self):
        if not self._view_frame.Show(true):
            self._view_frame.Raise()

#################################################################
# utility methods
#################################################################

    def _create_window(self):
        import modules.resources.python.slice3d_vwr_frame
        reload(modules.resources.python.slice3d_vwr_frame)

        # create main frame, make sure that when it's closed, it merely hides
        parent_window = self._moduleManager.get_module_view_parent_window()
        slice3d_vwr_frame = modules.resources.python.slice3d_vwr_frame.\
                            slice3d_vwr_frame
        self._view_frame = slice3d_vwr_frame(parent_window, id=-1,
                                             title='dummy')

        # fix for the grid
        self._view_frame.spointsGrid.SetSelectionMode(wxGrid.wxGridSelectRows)

        # add THREE the renderers
        self._threedRenderer = vtk.vtkRenderer()
        self._threedRenderer.SetBackground(0.5, 0.5, 0.5)
        self._view_frame.threedRWI.GetRenderWindow().AddRenderer(self.
                                                               _threedRenderer)
        self._ortho1Renderer = vtk.vtkRenderer()
        self._ortho1Renderer.SetBackground(0.5, 0.5, 0.5)
        self._view_frame.ortho1RWI.GetRenderWindow().AddRenderer(self.
                                                               _ortho1Renderer)
        self._ortho2Renderer = vtk.vtkRenderer()
        self._ortho2Renderer.SetBackground(0.5, 0.5, 0.5)
        self._view_frame.ortho2RWI.GetRenderWindow().AddRenderer(self.
                                                               _ortho2Renderer)

        # event handlers for the global control buttons
        EVT_BUTTON(self._view_frame, self._view_frame.pipelineButtonId,
                   lambda e, pw=self._view_frame, s=self,
                   rw=self._view_frame.threedRWI.GetRenderWindow():
                   s.vtkPipelineConfigure(pw, rw))

        def confPickedHandler(event):
            rwi = self._view_frame.threedRWI
            picker = rwi.GetPicker()
            path = picker.GetPath()
            if path:
                prop = path.GetFirstNode().GetProp()
                if prop:
                    self.vtkPipelineConfigure(self._view_frame,
                                              rwi.GetRenderWindow(),
                                              (prop,))

        EVT_BUTTON(self._view_frame, self._view_frame.confPickedButtonId,
                   confPickedHandler)

        EVT_BUTTON(self._view_frame, self._view_frame.resetButtonId,
                   lambda e, s=self: s._reset())

        
        # event logic for the selected points grid

        def pointsSelectAllCallback(event):
            self._view_frame.spointsGrid.SelectAll()

        def pointsDeselectAllCallback(event):
            self._view_frame.spointsGrid.ClearSelection()

        def pointsRemoveCallback(event):
            selRows = self._view_frame.spointsGrid.GetSelectedRows()
            print "SELROWS " + str(selRows)
            print "This should begin working somewhere after wxPython 2.4.0.1"
            if len(selRows):
                self._remove_cursors(selRows)

        EVT_BUTTON(self._view_frame, self._view_frame.pointsSelectAllButtonId,
                   pointsSelectAllCallback)
        EVT_BUTTON(self._view_frame,
                   self._view_frame.pointsDeselectAllButtonId,
                   pointsDeselectAllCallback)
        EVT_BUTTON(self._view_frame,
                   self._view_frame.pointsRemoveButtonId,
                   pointsRemoveCallback)

        # event logic for the voi panel
        def widgetEnabledCBoxCallback(event):
            if self._voi_widget.GetInput():
                if event.Checked():
                    self._voi_widget.On()
                    self.voiWidgetInteractionCallback(self._voi_widget, None)
                    self.voiWidgetEndInteractionCallback(self._voi_widget,
                                                         None)
                else:
                    self._voi_widget.Off()
            
            
        EVT_CHECKBOX(self._view_frame,
                     self._view_frame.voiPanel.widgetEnabledCboxId,
                     widgetEnabledCBoxCallback)

        # now the three ortho view pages + all callbacks
        orthoPanels = [self._view_frame.nbAxialPanel,
                       self._view_frame.nbCoronalPanel,
                       self._view_frame.nbSagittalPanel]

        for i in range(len(orthoPanels)):

            # first a callback for turning an IPW on or off
            def _eb_cb(i):
                ipw = self._ipws[i]
                if ipw.GetInput():
                    if orthoPanels[i].enabledCbox.GetValue():
                        ipw.On()
                    else:
                        ipw.Off()
        
            EVT_CHECKBOX(self._view_frame, orthoPanels[i].enabledCboxId,
                         lambda e, i=i:_eb_cb(i))

            # the store button
            EVT_BUTTON(self._view_frame, orthoPanels[i].storeId,
                       lambda e, i=i: self._store_cursor_cb(i))
            
            
            # now make callback for the ipw
            self._ipws[i].AddObserver('StartInteractionEvent',
                                      lambda e, o, i=i:
                                      self._ipw_start_interaction_cb(i))
            self._ipws[i].AddObserver('InteractionEvent',
                                      lambda e, o, i=i:
                                      self._ipw_interaction_cb(i))

        
        EVT_NOTEBOOK_PAGE_CHANGED(self._view_frame,
                                  self._view_frame.acsNotebookId,
                                  self._acs_nb_page_changed_cb)
        
        # attach close handler
        EVT_CLOSE(self._view_frame,
                  lambda e, s=self: s._view_frame.Show(false))

        # display the window
        self._view_frame.Show(true)

    def _remove_cursors(self, idxs):

        # we have to delete one by one from back to front
        idxs.sort()
        idxs.reverse()
        
        for idx in idxs:
            # remove the sphere actor from the renderer
            self._threedRenderer.RemoveActor(self._sel_points[idx]['sphere_actor'])
            # remove the text_actor (if any)
            if self._sel_points[idx]['text_actor']:
                self._threedRenderer.RemoveActor(self._sel_points[idx]['text_actor'])
            
            # then deactivate and disconnect the point widget
            pw = self._sel_points[idx]['point_widget']
            pw.SetInput(None)
            pw.Off()
            pw.SetInteractor(None)

            # remove the entries from the wxGrid
            self._view_frame.spointsGrid.DeleteRows(idx)

            # then remove it from our internal list
            del self._sel_points[idx]

        # rerender
        self._view_frame.threedRWI.Render()


        # and sync up vtk_points
        self._sync_vtk_points()
        
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
        self._cube_axes_actor2d.SetCamera(self._threedRenderer.GetActiveCamera())

        # calculate default window/level once
        (dmin,dmax) = input_data.GetScalarRange()
        iwindow = (dmax - dmin) / 2
        ilevel = dmin + iwindow

        input_data_source = input_data.GetSource()
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

        # colours of imageplanes; we will use these as keys
        ipw_cols = [(1,0,0), (0,1,0), (0,0,1)]

        idx = 2
        for ipw in self._ipws:
            ipw.DisplayTextOn()
            ipw.SetInteractor(self._view_frame.threedRWI)
            ipw.SetPlaneOrientation(idx)
            idx -= 1
            ipw.SetSliceIndex(0)
            ipw.GetPlaneProperty().SetColor(ipw_cols[idx])
            # this is not working yet, because the IPWs handling of
            # luts is somewhat broken at the moment
            ipw.SetLookupTable(lut)
            ipw.On()

        # how can I prevent the user from moving this with the
        # middle button?
        self._voi_widget.SetInteractor(self._view_frame.threedRWI)
        self._voi_widget.SetInput(input_data)
        self._voi_widget.PlaceWidget()
        self._voi_widget.SetPriority(0.6)
        #self._voi_widget.On()

        self._threedRenderer.ResetCamera()

        # whee, thaaaar she goes.
        self._view_frame.threedRWI.Render()

        # now also make sure that the notebook with slice config is updated
        self._acs_nb_page_changed_cb(None)

    def _store_cursor(self, cursor):

        # do we have data?
        if self._ipws[0].GetInput() is None:
            return

        # we first have to check that we don't have this pos already
        cursors = [i['cursor'] for i in self._sel_points]
        if cursor in cursors:
            return
        
        input_data = self._ipws[0].GetInput()
        ispacing = input_data.GetSpacing()
        iorigin = input_data.GetOrigin()
        # calculate real coords
        coords = map(operator.add, iorigin,
                     map(operator.mul, ispacing, cursor[0:3]))
        
        # we use a pointwidget

        pw = vtk.vtkPointWidget()
        pw.SetInput(input_data)
        pw.PlaceWidget()
        pw.SetPosition(coords)
        # make priority higher than the default of vtk3DWidget so
        # that imageplanes behind us don't get selected the whole time
        pw.SetPriority(0.6)
        pw.SetInteractor(self._view_frame.threedRWI)
        pw.AllOff()
        pw.On()

        ss = vtk.vtkSphereSource()
        bounds = input_data.GetBounds()
        ss.SetRadius((bounds[1] - bounds[0]) / 50.0)
        sm = vtk.vtkPolyDataMapper()
        sm.SetInput(ss.GetOutput())
        sa = vtk.vtkActor()
        sa.SetMapper(sm)
        sa.SetPosition(coords)
        sa.GetProperty().SetColor(1.0,0.0,0.0)
        self._threedRenderer.AddActor(sa)

        # first get the name of the point that we are going to store
        nb = self._view_frame.acsNotebook
        cur_panel = nb.GetPage(nb.GetSelection())
        cursor_name = cur_panel.cursorNameCombo.GetValue()

        if len(cursor_name) > 0:
            name_text = vtk.vtkVectorText()
            name_text.SetText(cursor_name)
            name_mapper = vtk.vtkPolyDataMapper()
            name_mapper.SetInput(name_text.GetOutput())
            ta = vtk.vtkFollower()
            ta.SetMapper(name_mapper)
            ta.GetProperty().SetColor(1.0, 1.0, 0.0)
            ta.SetPosition(coords)
            ta_bounds = ta.GetBounds()
            ta.SetScale((bounds[1] - bounds[0]) / 7.0 /
                        (ta_bounds[1] - ta_bounds[0]))
            self._threedRenderer.AddActor(ta)
            ta.SetCamera(self._threedRenderer.GetActiveCamera())
        else:
            ta = None


        def pw_ei_cb(pw, evt_name):
            # make sure our output is good
            self._sync_vtk_points()

        pw.AddObserver('StartInteractionEvent', lambda pw, evt_name,
                       input_data=input_data, s=self:
                       s.pointwidget_interaction_cb(pw, evt_name, input_data))
        pw.AddObserver('InteractionEvent', lambda pw, evt_name,
                       input_data=input_data, s=self:
                       s.pointwidget_interaction_cb(pw, evt_name, input_data))
        pw.AddObserver('EndInteractionEvent', pw_ei_cb)
        
        # store the cursor (discrete coords) the coords and the actor
        self._sel_points.append({'cursor' : cursor, 'coords' : coords,
                                 'name' : cursor_name,
                                 'point_widget' : pw,
                                 'sphere_actor' : sa,
                                 'text_actor' : ta})

        
        self._view_frame.spointsGrid.AppendRows()
	self._view_frame.spointsGrid.AdjustScrollbars()        
        row = self._view_frame.spointsGrid.GetNumberRows() - 1
        self._syncGridRowToSelPoints(row)
        
        # make sure self._vtk_points is up to date
        self._sync_vtk_points()

        self._view_frame.threedRWI.Render()

    def _syncGridRowToSelPoints(self, row):
        # *sniff* *sob* It's unreadable, but why's it so pretty?
        # this just formats the real point
        cursor = self._sel_points[row]['cursor']
        pos_str = "%s, %s, %s" % tuple(cursor[0:3])
        self._view_frame.spointsGrid.SetCellValue(row, 0, pos_str)
        self._view_frame.spointsGrid.SetCellValue(row, 1, str(cursor[3]))

    def _sync_vtk_points(self):
        """Sync up the output vtkPoints and names to _sel_points.
        
        We play it safe, as the number of points in this list is usually
        VERY low.
        """
        
        # first make sure it's empty
        self._vtk_points.SetNumberOfPoints(0)
        # delete all elements, but keep the actual object around
        # so that all bindings to it (on input modules) remain the same
        del self._vtk_points_names[:]
        # then transfer everything
        for i in self._sel_points:
            x,y,z,v = i['cursor']
            self._vtk_points.InsertNextPoint(x,y,z)
            self._vtk_points_names.append(i['name'])

        # and then make sure the vtkPoints knows that it has been modified
        self._vtk_points.Modified()
        
#################################################################
# callbacks
#################################################################

    def _acs_nb_page_changed_cb(self, event):
        nb = self._view_frame.acsNotebook
        cur_panel = nb.GetPage(nb.GetSelection())
        if self._ipws[nb.GetSelection()].GetEnabled():
            cur_panel.enabledCbox.SetValue(true)
        else:
            cur_panel.enabledCbox.SetValue(false)

    def _ipw_start_interaction_cb(self, i):
        self._view_frame.acsNotebook.SetSelection(i)
        self._ipw_interaction_cb(i)

    def _ipw_interaction_cb(self, i):
        cd = 4 * [0.0]
        if self._ipws[i].GetCursorData(cd):
            nb = self._view_frame.acsNotebook
            cur_panel = nb.GetPage(nb.GetSelection())
            self._current_cursors[i] = cd
            cstring = str(cd[0:3]) + " = " + str(cd[3])
            cur_panel.cursorText.SetValue(cstring)

    def pointwidget_interaction_cb(self, pw, evt_name, input_data):
        # we have to find pw in our list
        pwidgets = map(lambda i: i['point_widget'], self._sel_points)
        if pw in pwidgets:
            idx = pwidgets.index(pw)
            # toggle the selection for this point in our list
            self._view_frame.spointsGrid.SelectRow(idx)

            # get its position and transfer it to the sphere actor that
            # we use
            pos = pw.GetPosition()
            self._sel_points[idx]['sphere_actor'].SetPosition(pos)

            # also update the text_actor (if appropriate)
            ta = self._sel_points[idx]['text_actor']
            if ta:
                ta.SetPosition(pos)

            # then we have to update our internal record of this point
            ispacing = input_data.GetSpacing()
            iorigin = input_data.GetOrigin()
            x,y,z = map(round,
                        map(operator.div,
                        map(operator.sub, pos, iorigin), ispacing))
            val = input_data.GetScalarComponentAsFloat(x,y,z, 0)
            # the cursor is a tuple with discrete position and value
            self._sel_points[idx]['cursor'] = (x,y,z,val)
            # 'coords' is the world coordinates
            self._sel_points[idx]['coords'] = pos

            self._syncGridRowToSelPoints(idx)
            

    # DEPRECATED CODE
    def _rw_ortho_pick_cb(self, wxvtkrwi):
        (cx,cy) = wxvtkrwi.GetEventPosition()
        r_idx = self._rwis.index(wxvtkrwi)

        # there has to be data in this pipeline before we can go on
        if len(self._ortho_pipes[r_idx - 1]):
        
            # instantiate WorldPointPicker and use it to get the World Point
            # that we've selected
            wpp = vtk.vtkWorldPointPicker()
            wpp.Pick(cx,cy,0,self._threedRenderers[r_idx])
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
    
    # DEPRECATED CODE
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

    # DEPRECATED CODE
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
        """Call back for the store cursor button.

        Calls store cursor method on [x,y,z,v].
        """
        self._store_cursor(self._current_cursors[i])
        
    def voiWidgetInteractionCallback(self, o, e):
        planes = vtk.vtkPlanes()
        o.GetPlanes(planes)
        bounds =  planes.GetPoints().GetBounds()

        # first set bounds
        self._view_frame.voiPanel.boundsText.SetValue(
            "(%.2f %.2f %.2f %.2f %.2f %.2f) mm" %
            bounds)

        # then set discrete extent (volume relative)
        input_data = self._extractVOI.GetInput()
        ispacing = input_data.GetSpacing()
        iorigin = input_data.GetOrigin()
        # calculate discrete coords
        bounds = planes.GetPoints().GetBounds()
        voi = 6 * [0]
        # excuse the for loop :)
        for i in range(6):
            voi[i] = round((bounds[i] - iorigin[i / 2]) / ispacing[i / 2])
        # store the VOI (this is a shallow copy)
        self._currentVOI = voi
        # display the discrete extent
        self._view_frame.voiPanel.extentText.SetValue(
            "(%d %d %d %d %d %d)" % tuple(voi))


    def voiWidgetEndInteractionCallback(self, o, e):
        # adjust the vtkExtractVOI with the latest coords
        self._extractVOI.SetVOI(self._currentVOI)


    def inputModifiedCallback(self, o, e):
        print "DATA MODIFIED"
        self._view_frame.threedRWI.Render()
        

    
    
        

