# slice3d_vwr.py copyright (c) 2002 Charl P. Botha <cpbotha@ieee.org>
# $Id: slice3d_vwr.py,v 1.34 2003/03/05 17:04:15 cpbotha Exp $
# next-generation of the slicing and dicing dscas3 module

from genUtils import logError
from genMixins import subjectMixin
from moduleBase import moduleBase
from moduleMixins import vtkPipelineConfigModuleMixin
import vtk
from wxPython.wx import *
from wxPython.grid import *
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor
import operator

# -------------------------------------------------------------------------
class directionPipeline:
    """Class encapsulating all logic behind a single direction.

    This class contains the IPWs and related paraphernalia for all layers
    (primary + overlays) representing a single view direction.  It optionally
    has its own window with an orthogonal view.
    """

    def __init__(self):
        pass


# -------------------------------------------------------------------------
class outputSelectedPoints(list, subjectMixin):
    """class for passing selected points to an output port.

    Derived from list as base and the subject/observer mixin.
    """
    
    def __init__(self):
        list.__init__(self)
        subjectMixin.__init__(self)

    def close(self):
        subjectMixin.close(self)

# -------------------------------------------------------------------------
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
                         'vtkActor' : None, 'ipw' : None}
                       for i in range(self._numDataInputs)]
        # then the window containing the renderwindows
        self._viewFrame = None
        # the imageplanewidgets: a 3-element (axial, coronal, sagittal) list
        # of lists of IPWs (each direction list contains the primary IPW
        # as well as all overlays)
        self._ipws = [[] for i in range(3)]
        # list of current cursors, one cursor for each ipw
        self._current_cursors = []
        # the renderers corresponding to the render windows
        self._threedRenderer = None
        self._orthoRenderers = [None for i in range(2)]

        # list of selected points (we can make this grow or be overwritten)
        self._selectedPoints = []
        # this will be passed on as input to the next component
        self._outputSelectedPoints = outputSelectedPoints()
        
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

        self._current_cursors = [[0,0,0,0] for i in self._ipws]

        # create 2 empty orthoView pipelines
        self._orthoViews = [{'planeSources' : [],
                             'planeActors' : [],
                             'textureMapToPlanes' : [],
                             'direction' : -1} for i in range(2)]
        
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

        # don't forget to call the mixin close() methods
        vtkPipelineConfigModuleMixin.close(self)
        
        # unbind everything that we bound in our __init__
        del self._outline_source
        del self._outline_actor
        del self._cube_axes_actor2d
        del self._voi_widget
        del self._extractVOI
        
	del self._ipws

        # take care of all our bindings to renderers
        del self._threedRenderer
        del self._orthoRenderers

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
	#self._viewFrame.Show(0)

        self._viewFrame.threedRWI.GetRenderWindow().SetSize(10,10)
        self._viewFrame.threedRWI.GetRenderWindow().WindowRemap()        
        self._viewFrame.ortho1RWI.GetRenderWindow().SetSize(10,10)
        self._viewFrame.ortho1RWI.GetRenderWindow().WindowRemap()        
        self._viewFrame.ortho2RWI.GetRenderWindow().SetSize(10,10)
        self._viewFrame.ortho2RWI.GetRenderWindow().WindowRemap()        
        
        # all the RenderWindow()s are now reparented, so we can destroy
        # the containing frame
        self._viewFrame.Destroy()
	# unbind the _view_frame binding
	del self._viewFrame
	
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
                    self._ipws[0][0].GetInput().RemoveObserver(
                        self._inputs[idx]['observerID'])
                    self._inputs[idx]['observerID'] = -1
                
                # by definition, this will be the first and only layer of IPWS
                for ipwDir in self._ipws:
                    ipwDir[0].Off()
                    ipwDir[0].SetInput(None)
                    ipwDir[0].SetInteractor(None)
                    # remove the binding! - this doesn't exist anymore
                    del ipwDir[0]

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

                # we've disconnected a primary, also destroy orthos
                self._destroyOrthoView(0)
                self._destroyOrthoView(1)

            elif self._inputs[idx]['Connected'] == 'Overlay':
                self._inputs[idx]['Connected'] = None

                # we keep track of the axial ipw, because the index of the
                # overlay can change
                ipw = self._inputs[idx]['ipw']
                
                # remove our observer
                if self._inputs[idx]['observerID'] >= 0:
                    ipw.GetInput().RemoveObserver(
                        self._inputs[idx]['observerID'])
                    self._inputs[idx]['observerID'] = -1

                # disconnect this overlay
                # first search for it in the axial direction
                layerIdx = self._ipws[0].index(ipw)

                for ipwDir in self._ipws:
                    ipwDir[layerIdx].Off()
                    ipwDir[layerIdx].SetInput(None)
                    ipwDir[layerIdx].SetInteractor(None)
                    del ipwDir[layerIdx]

                # finally take care of the 'ipw' as well!
                self._inputs[idx]['ipw'] = None

                # we've removed the overlay, the orthos would like to know
                # about that
                self._connectOrthoViewToDirection(0)
                self._connectOrthoViewToDirection(1)                
                
        # END of if input_stream is None clause -----------------------------

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
                self._viewFrame.threedRWI.Render()

                # connect an event handler to the data
                oid = input_stream.AddObserver('ModifiedEvent',
                                               self.inputModifiedCallback)
                self._inputs[idx]['observerID'] = oid
                
                
            elif input_stream.IsA('vtkImageData'):

                # if we already have an ImageData input, we can't take anymore
                for input in self._inputs:
                    if input['Connected'] == 'vtkImageData':

                        # check the overlay for size and spacing
                        input_stream.Update()

                        # get primary IPW in axial direction
                        main_input = self._ipws[0][0].GetInput()

                        if input_stream.GetWholeExtent() == \
                               main_input.GetWholeExtent() and \
                               input_stream.GetSpacing() == \
                               main_input.GetSpacing():
                            
                            input_stream.Update()

                            
                            for direction in range(3):
                                ipw = vtk.vtkImagePlaneWidget()
                                self._ipws[direction].append(ipw)
                                ipw.SetInput(input_stream)
                                ipw.UserControlledLookupTableOn()

                            # we store the first ipw
                            self._inputs[idx]['ipw'] = self._ipws[0][-1]

                            oid = input_stream.AddObserver(
                                'ModifiedEvent',
                                self.inputModifiedCallback)
                            self._inputs[idx]['observerID'] = oid

                            self._resetOverlays()

                            self._viewFrame.threedRWI.Render()

                            # now make sure the orthos are happy (we've
                            # added an overlay)
                            self._connectOrthoViewToDirection(0)
                            self._connectOrthoViewToDirection(1)
                            self._viewFrame.ortho1RWI.Render()
                            self._viewFrame.ortho2RWI.Render()
                            
                            self._inputs[idx]['Connected'] = 'Overlay'

                            return
                            
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

                # set the same picker for each vtkIPW
                picker = vtk.vtkCellPicker()

                # by definition, our self._ipws will be a 3-element list
                # of empty lists
                for direction in range(3):
                    if self._ipws[direction]:
                        raise Exception, "Yikes, self._ipws has non-0 lists!"
                    
                    ipw = vtk.vtkImagePlaneWidget()
                    self._ipws[direction].append(ipw)
                    ipw.SetInput(input_stream)
                    ipw.SetPicker(picker)

                    # now make callback for the ipw
                    ipw.AddObserver('StartInteractionEvent',
                                    lambda e, o, d=direction:
                                    self._ipwStartInteractionCallback(d))
                    ipw.AddObserver('InteractionEvent',
                                    lambda e, o, d=direction:
                                    self._ipwInteractionCallback(d))
                    ipw.AddObserver('EndInteractionEvent',
                                    lambda e, o, d=direction:
                                    self._ipwEndInteractionCallback(d))
                    

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

                # we have a new primary data set, so we can say where the
                # orthos go
                self._connectOrthoViewToDirection(0, 0)
                self._connectOrthoViewToDirection(1, 1)

                # reset everything, including ortho camera
                self._reset()

                self._viewFrame.threedRWI.Render()
                self._inputs[idx]['Connected'] = 'vtkImageData'

            else:
                raise TypeError, "Wrong input type!"

        
        # make sure we catch any errors!
        self._moduleManager.vtk_poll_error()

        
    def getOutputDescriptions(self):
        return ('Selected points',
                'Volume of Interest (vtkStructuredPoints)')
        
    def getOutput(self, idx):
        if idx == 0:
            return self._outputSelectedPoints
        else:
            return self._extractVOI.GetOutput()

    def view(self):
        if not self._viewFrame.Show(true):
            self._viewFrame.Raise()

#################################################################
# utility methods
#################################################################



    def _connectOrthoViewToDirection(self, orthoIdx, direction=-1):
        """Connect the orthoIdx'th orthoView to direction.

        Because we can't really rely on any state whatsoever, this
        call first destroys all objects belonging to all ortho layers in
        this direction and then recreates them.
        """

        # if direction is -1, use existing direction metadata
        # if that is also -1, go to defaults
        if direction < 0:
            direction = self._orthoViews[orthoIdx]['direction']
            if direction < 0:
                direction = orthoIdx

        # first take care of current pipeline
        self._destroyOrthoView(orthoIdx)

        orthoView = self._orthoViews[orthoIdx]
        # go through each layer in the ipws of this direction, setting up
        # the little pipeline
        for layer in range(len(self._ipws[direction])):
            orthoView['planeSources'].append(vtk.vtkPlaneSource())
            orthoView['planeActors'].append(vtk.vtkActor())

            tm2p = vtk.vtkTextureMapToPlane()
            orthoView['textureMapToPlanes'].append(tm2p)
            tm2p.AutomaticPlaneGenerationOff()
            tm2p.SetInput(orthoView['planeSources'][-1].\
                          GetOutput())
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInput(tm2p.GetOutput())

            orthoView['planeActors'][-1].SetMapper(mapper)
            otherTexture = self._ipws[direction][layer].GetTexture()

            # we don't just use the texture, else VTK goes mad re-uploading
            # the same texture unnecessarily... let's just make use of the
            # same input, we get much more effective use of the host->GPU bus
            texture = vtk.vtkTexture()
            texture.SetInterpolate(otherTexture.GetInterpolate())
            texture.SetQuality(otherTexture.GetQuality())
            texture.MapColorScalarsThroughLookupTableOff()
            texture.RepeatOff()
            texture.SetInput(otherTexture.GetInput())
            
            orthoView['planeActors'][-1].SetTexture(texture)

            self._orthoRenderers[orthoIdx].AddActor(
                orthoView['planeActors'][-1])

            orthoView['direction'] = direction

            # and of course end with a sync!
            self._syncOrthoViewWithIPW(orthoIdx)


    def _create_window(self):
        import modules.resources.python.slice3d_vwr_frame
        reload(modules.resources.python.slice3d_vwr_frame)

        # create main frame, make sure that when it's closed, it merely hides
        parent_window = self._moduleManager.get_module_view_parent_window()
        slice3d_vwr_frame = modules.resources.python.slice3d_vwr_frame.\
                            slice3d_vwr_frame
        self._viewFrame = slice3d_vwr_frame(parent_window, id=-1,
                                             title='dummy')

        # fix for the grid
        self._viewFrame.spointsGrid.SetSelectionMode(wxGrid.wxGridSelectRows)

        # add THREE the renderers
        self._threedRenderer = vtk.vtkRenderer()
        self._threedRenderer.SetBackground(0.5, 0.5, 0.5)
        self._viewFrame.threedRWI.GetRenderWindow().AddRenderer(self.
                                                               _threedRenderer)
        
        orthoRWIs = [self._viewFrame.ortho1RWI, self._viewFrame.ortho2RWI]
        for orthoIdx in range(len(self._orthoRenderers)):
            self._orthoRenderers[orthoIdx] = vtk.vtkRenderer()
            self._orthoRenderers[orthoIdx].SetBackground(0.5, 0.5, 0.5)
            rw = orthoRWIs[orthoIdx].GetRenderWindow()
            rw.AddRenderer(self._orthoRenderers[orthoIdx])

            istyle = vtk.vtkInteractorStyleImage()
            orthoRWIs[orthoIdx].SetInteractorStyle(istyle)
        
        # event handlers for the global control buttons
        EVT_BUTTON(self._viewFrame, self._viewFrame.pipelineButtonId,
                   lambda e, pw=self._viewFrame, s=self,
                   rw=self._viewFrame.threedRWI.GetRenderWindow():
                   s.vtkPipelineConfigure(pw, rw))

        def confPickedHandler(event):
            rwi = self._viewFrame.threedRWI
            picker = rwi.GetPicker()
            path = picker.GetPath()
            if path:
                prop = path.GetFirstNode().GetProp()
                if prop:
                    self.vtkPipelineConfigure(self._viewFrame,
                                              rwi.GetRenderWindow(),
                                              (prop,))

        #EVT_BUTTON(self._viewFrame, self._viewFrame.confPickedButtonId,
        #           confPickedHandler)

        EVT_BUTTON(self._viewFrame, self._viewFrame.resetButtonId,
                   lambda e, s=self: s._reset())


        def pointsSelectAllCallback(event):
            self._viewFrame.spointsGrid.SelectAll()

        def pointsDeselectAllCallback(event):
            self._viewFrame.spointsGrid.ClearSelection()

        def pointsRemoveCallback(event):
            selRows = self._viewFrame.spointsGrid.GetSelectedRows()
            print "SELROWS " + str(selRows)
            print "This should begin working somewhere after wxPython 2.4.0.1"
            if len(selRows):
                self._remove_cursors(selRows)

        EVT_BUTTON(self._viewFrame, self._viewFrame.pointsSelectAllButtonId,
                   pointsSelectAllCallback)
        EVT_BUTTON(self._viewFrame,
                   self._viewFrame.pointsDeselectAllButtonId,
                   pointsDeselectAllCallback)
        EVT_BUTTON(self._viewFrame,
                   self._viewFrame.pointsRemoveButtonId,
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
            
            
        EVT_CHECKBOX(self._viewFrame,
                     self._viewFrame.voiPanel.widgetEnabledCboxId,
                     widgetEnabledCBoxCallback)

        # now the three ortho view pages + all callbacks
        orthoPanels = [self._viewFrame.nbAxialPanel,
                       self._viewFrame.nbCoronalPanel,
                       self._viewFrame.nbSagittalPanel]

        for i in range(len(orthoPanels)):

            # first a callback for turning an IPW on or off
            def _eb_cb(i):
                ipw = self._ipws[i][0]
                if ipw.GetInput():
                    if orthoPanels[i].enabledCbox.GetValue():
                        ipw.On()
                        # and if there are overlays, switch them back on
                        for overlay_ipw in self._ipws[i][1:]:
                            overlay_ipw.On()
                                
                        orthoPanels[i].interactionCbox.Enable(1)
                        orthoPanels[i].pushSliceLabel.Enable(1)
                        orthoPanels[i].pushSliceSpinCtrl.Enable(1)
                        
                    else:
                        ipw.Off()
                        # also switch off the overlays...
                        for overlay_ipw in self._ipws[i][1:]:
                            overlay_ipw.Off()
                            
                        orthoPanels[i].interactionCbox.Enable(0)
                        orthoPanels[i].pushSliceLabel.Enable(0)
                        orthoPanels[i].pushSliceSpinCtrl.Enable(0)
                        
        
            EVT_CHECKBOX(self._viewFrame, orthoPanels[i].enabledCboxId,
                         lambda e, i=i:_eb_cb(i))

            def _ib_cb(i):
                ipw = self._ipws[i][0]
                if ipw.GetInput():
                    if orthoPanels[i].interactionCbox.GetValue():
                        ipw.SetInteraction(1)
                    else:
                        ipw.SetInteraction(0)
                

            EVT_CHECKBOX(self._viewFrame, orthoPanels[i].interactionCboxId,
                         lambda e, i=i: _ib_cb(i))

            def _ps_cb(i):
                ipw = self._ipws[i][0]
                if ipw.GetInput():
                    val = orthoPanels[i].pushSliceSpinCtrl.GetValue()
                    if val:
                        ipw.GetPolyDataSource().Push(val)
                        ipw.UpdatePlacement()
                        orthoPanels[i].pushSliceSpinCtrl.SetValue(0)
                        self._ipwEndInteractionCallback(i)
                        self._viewFrame.threedRWI.Render()

            EVT_SPINCTRL(self._viewFrame, orthoPanels[i].pushSliceSpinCtrlId,
                         lambda e, i=i: _ps_cb(i))

            # the store button
            EVT_BUTTON(self._viewFrame, orthoPanels[i].storeId,
                       lambda e, i=i: self._storeCursorCallback(i))
            
        EVT_NOTEBOOK_PAGE_CHANGED(self._viewFrame,
                                  self._viewFrame.acsNotebookId,
                                  self._acs_nb_page_changed_cb)

        # clicks directly in the window for picking
        self._viewFrame.threedRWI.AddObserver('LeftButtonPressEvent',
                                               self._rwiLeftButtonCallback)
        
        # attach close handler
        EVT_CLOSE(self._viewFrame,
                  lambda e, s=self: s._view_frame.Show(false))

        # display the window
        self._viewFrame.Show(true)

    def _destroyOrthoView(self, orthoIdx):
        """Disconnect all inputs for the orthoIdx'th orthoView and then
        destroy all objects.
        """

        orthoView = self._orthoViews[orthoIdx]
        if orthoView['planeSources']:
            direction = orthoView['direction']
            for layer in range(len(orthoView['planeSources'])):
                             actor = orthoView['planeActors'][layer]
                             self._orthoRenderers[orthoIdx].RemoveActor(actor)
                             # this will remove the current texture,
                             # freeing it for destruction
                             actor.SetTexture(None)


            # now nuke the whole structure
            self._orthoViews[orthoIdx] = {'planeSources' : [],
                                          'planeActors' : [],
                                          'textureMapToPlanes' : [],
                                          'direction' : -1}

    def _remove_cursors(self, idxs):

        # we have to delete one by one from back to front
        idxs.sort()
        idxs.reverse()
        
        for idx in idxs:
            # remove the sphere actor from the renderer
            self._threedRenderer.RemoveActor(self._selectedPoints[idx]['sphere_actor'])
            # remove the text_actor (if any)
            if self._selectedPoints[idx]['text_actor']:
                self._threedRenderer.RemoveActor(self._selectedPoints[idx]['text_actor'])
            
            # then deactivate and disconnect the point widget
            pw = self._selectedPoints[idx]['point_widget']
            pw.SetInput(None)
            pw.Off()
            pw.SetInteractor(None)

            # remove the entries from the wxGrid
            self._viewFrame.spointsGrid.DeleteRows(idx)

            # then remove it from our internal list
            del self._selectedPoints[idx]

            # rerender
            self._viewFrame.threedRWI.Render()

            # and sync up output points
            self._syncOutputSelectedPoints()
        
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
        if len(self._ipws[0]) <= 0:
            return

        input_data = self._ipws[0][0].GetInput()

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

        # we want to do only the primaries here
        idx = 2
        for directionIdx in range(3):
            ipw = self._ipws[directionIdx][0]
            ipw.DisplayTextOn()
            ipw.SetInteractor(self._viewFrame.threedRWI)
            ipw.SetPlaneOrientation(idx)
            idx -= 1
            ipw.SetSliceIndex(0)
            ipw.GetPlaneProperty().SetColor(ipw_cols[idx])
            # this is not working yet, because the IPWs handling of
            # luts is somewhat broken at the moment
            ipw.SetLookupTable(lut)
            ipw.On()

        # reset the VOI widget
        self._voi_widget.SetInteractor(self._viewFrame.threedRWI)
        self._voi_widget.SetInput(input_data)
        self._voi_widget.PlaceWidget()
        self._voi_widget.SetPriority(0.6)
        #self._voi_widget.On()

        self._threedRenderer.ResetCamera()

        # make sure the overlays follow  suit
        self._resetOverlays()

        # whee, thaaaar she goes.
        self._viewFrame.threedRWI.Render()

        # and the orthos
        self._setupOrthoViewCamera(0)
        self._setupOrthoViewCamera(1)        
        self._viewFrame.ortho1RWI.Render()
        self._viewFrame.ortho2RWI.Render()

        # now also make sure that the notebook with slice config is updated
        #self._acs_nb_page_changed_cb(None)

    def _setupOrthoViewCamera(self, orthoIdx):
        """Once the orthoView has been connected to a particular IPW, this
        method will make sure that the camera points orthogonally at it.
        """
        
        # now we know the plane geometry is synced with the IPW
        self._syncOrthoViewWithIPW(orthoIdx)
        # just get the first planesource
        planeSource = self._orthoViews[orthoIdx]['planeSources'][0]
        # let's setup the camera
        icam = self._orthoRenderers[orthoIdx].GetActiveCamera()
        icam.SetPosition(planeSource.GetCenter()[0],
                         planeSource.GetCenter()[1], 10)
        icam.SetFocalPoint(planeSource.GetCenter())
        icam.OrthogonalizeViewUp()
        icam.SetViewUp(0,1,0)
        icam.SetClippingRange(1,11)
        v2 = map(operator.sub, planeSource.GetPoint2(),
                 planeSource.GetOrigin())
        n2 = vtk.vtkMath.Normalize(v2)
        icam.SetParallelScale(n2 / 2.0)
        icam.ParallelProjectionOn()
        
    def _resetOverlays(self):
        # first check if we have overlays
        if len(self._ipws[0]) > 1:
            # iterate through overlay layers
            for layer in range(len(self._ipws[0]))[1:]:
                lut = vtk.vtkLookupTable()            
                inputStream = self._ipws[0][layer].GetInput()
                minv, maxv = inputStream.GetScalarRange()
                lut.SetTableRange((minv,maxv))
                lut.SetAlphaRange((0.0, 1.0))
                lut.SetValueRange((1.0, 1.0))
                lut.SetSaturationRange((1.0, 1.0))
                lut.Build()

                idx = 2
                for direction in range(3):
                    ipw = self._ipws[direction][layer]
                    
                    ipw.SetInteractor(self._viewFrame.threedRWI)
                    ipw.SetPlaneOrientation(idx)
                    idx -= 1
                    ipw.SetSliceIndex(0)
                    #ipw.GetPlaneProperty().SetColor(ipw_cols[idx])
                    
                    ipw.SetLookupTable(lut)
                    ipw.On()
                    ipw.InteractionOff()

        self._syncOverlays()
        
    def _storeSurfacePoint(self, pointId, actor):
        polyData = actor.GetMapper().GetInput()
        if polyData:
            xyz = polyData.GetPoint(pointId)
        else:
            # something really weird went wrong
            return

        worlds = [i['world'] for i in self._selectedPoints]
        if xyz in worlds:
            return

        if self._ipws[0]:
            inputData = self._ipws[0][0].GetInput()
        else:
            inputData = None
            
        if inputData:
            # get the discrete coords of this point
            ispacing = inputData.GetSpacing()
            iorigin = inputData.GetOrigin()
            discrete = map(round,
                           map(operator.div,
                               map(operator.sub, xyz, iorigin), ispacing))
            val = inputData.GetScalarComponentAsFloat(discrete[0],discrete[1],
                                                      discrete[2], 0)
        else:
            discrete = (0, 0, 0)
            val = 0

        self._storePoint(discrete, xyz, val)

    def _storeCursor(self, cursor):
        """Store the point represented by the cursor parameter.

        cursor is a 4-tuple with the discrete (data-relative) xyz coords and
        the value at that point.
        """
        
        # do we have volume data?
        if self._ipws[0][0].GetInput() is None:
            return

        # we first have to check that we don't have this pos already
        discretes = [i['discrete'] for i in self._selectedPoints]
        if tuple(cursor[0:3]) in discretes:
            return
        
        input_data = self._ipws[0][0].GetInput()
        ispacing = input_data.GetSpacing()
        iorigin = input_data.GetOrigin()
        # calculate real coords
        world = map(operator.add, iorigin,
                    map(operator.mul, ispacing, cursor[0:3]))

        self._storePoint(tuple(cursor[0:3]), tuple(world), cursor[3])

    def _storePoint(self, discrete, world, value):

        bounds = self._threedRenderer.ComputeVisiblePropBounds()        
        
        # we use a pointwidget
        pw = vtk.vtkPointWidget()
        #pw.SetInput(inputData)
        pw.PlaceWidget(bounds[0], bounds[1], bounds[2], bounds[3], bounds[4],
                       bounds[5])
        pw.SetPosition(world)
        # make priority higher than the default of vtk3DWidget so
        # that imageplanes behind us don't get selected the whole time
        pw.SetPriority(0.6)
        pw.SetInteractor(self._viewFrame.threedRWI)
        pw.AllOff()
        pw.On()

        ss = vtk.vtkSphereSource()
        #bounds = inputData.GetBounds()

        ss.SetRadius((bounds[1] - bounds[0]) / 50.0)
        sm = vtk.vtkPolyDataMapper()
        sm.SetInput(ss.GetOutput())
        sa = vtk.vtkActor()
        sa.SetMapper(sm)
        sa.SetPosition(world)
        sa.GetProperty().SetColor(1.0,0.0,0.0)
        self._threedRenderer.AddActor(sa)

        # first get the name of the point that we are going to store
        nb = self._viewFrame.acsNotebook
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
            ta.SetPosition(world)
            ta_bounds = ta.GetBounds()
            ta.SetScale((bounds[1] - bounds[0]) / 7.0 /
                        (ta_bounds[1] - ta_bounds[0]))
            self._threedRenderer.AddActor(ta)
            ta.SetCamera(self._threedRenderer.GetActiveCamera())
        else:
            ta = None


        def pw_ei_cb(pw, evt_name):
            # make sure our output is good
            self._syncOutputSelectedPoints()

        pw.AddObserver('StartInteractionEvent', lambda pw, evt_name,
                       s=self:
                       s._pointWidgetInteractionCallback(pw, evt_name))
        pw.AddObserver('InteractionEvent', lambda pw, evt_name,
                       s=self:
                       s._pointWidgetInteractionCallback(pw, evt_name))
        pw.AddObserver('EndInteractionEvent', pw_ei_cb)
        
        # store the cursor (discrete coords) the coords and the actor
        self._selectedPoints.append({'discrete' : tuple(discrete),
                                     'world' : tuple(world),
                                     'value' : value,
                                     'name' : cursor_name,
                                     'point_widget' : pw,
                                     'sphere_actor' : sa,
                                     'text_actor' : ta})

        
        self._viewFrame.spointsGrid.AppendRows()
	self._viewFrame.spointsGrid.AdjustScrollbars()        
        row = self._viewFrame.spointsGrid.GetNumberRows() - 1
        self._syncGridRowToSelPoints(row)
        
        # make sure self._outputSelectedPoints is up to date
        self._syncOutputSelectedPoints()

        self._viewFrame.threedRWI.Render()

    def _syncGridRowToSelPoints(self, row):
        # *sniff* *sob* It's unreadable, but why's it so pretty?
        # this just formats the real point
        discrete = self._selectedPoints[row]['discrete']
        world = self._selectedPoints[row]['world']
        value = self._selectedPoints[row]['value']
        discreteStr = "%.0f, %.0f, %.0f" % discrete
        worldStr = "%.2f, %.2f, %.2f" % world
        self._viewFrame.spointsGrid.SetCellValue(row, 0, worldStr)
        self._viewFrame.spointsGrid.SetCellValue(row, 1, discreteStr)

        self._viewFrame.spointsGrid.SetCellValue(row, 2, str(value))

    def _syncOverlay(self, direction):

        # check that we do have overlays for this direction
        if len(self._ipws[direction]) > 1:
            # we know this is a vtkPlaneSource
            pds1 = self._ipws[direction][0].GetPolyDataSource()

            for ipw in self._ipws[direction][1:]:
                pds2 = ipw.GetPolyDataSource()
                pds2.SetOrigin(pds1.GetOrigin())
                pds2.SetPoint1(pds1.GetPoint1())
                pds2.SetPoint2(pds1.GetPoint2())
            
                ipw.UpdatePlacement()
        
    def _syncOverlays(self):
        for direction in range(3):
            self._syncOverlay(direction)

    def _syncOrthoViewWithIPW(self, orthoIdx):
        orthoView = self._orthoViews[orthoIdx]
        
        # find IPW that we're syncing with
        direction = orthoView['direction']
        ipwDir = self._ipws[direction]

        # just use the primary IPW for this direction
        ipw = ipwDir[0]
        
        # vectorN is pointN - origin
        v1 = [0,0,0]
        ipw.GetVector1(v1)
        n1 = vtk.vtkMath.Normalize(v1)
        v2 = [0,0,0]
        ipw.GetVector2(v2)
        n2 = vtk.vtkMath.Normalize(v2)

        roBounds = ipw.GetResliceOutput().GetBounds()

        for layer in range(len(orthoView['planeSources'])):
            planeSource = orthoView['planeSources'][layer]
            planeSource.SetOrigin(0,0,0)
            planeSource.SetPoint1(n1, 0, 0)
            planeSource.SetPoint2(0, n2, 0)

            tm2p = orthoView['textureMapToPlanes'][layer]
            tm2p.SetOrigin(0,0,0)
            tm2p.SetPoint1(roBounds[1] - roBounds[0], 0, 0)
            tm2p.SetPoint2(0, roBounds[3] - roBounds[2], 0)


    def _syncOutputSelectedPoints(self):
        """Sync up the output vtkPoints and names to _sel_points.
        
        We play it safe, as the number of points in this list is usually
        VERY low.
        """

        del self._outputSelectedPoints[:]

        # then transfer everything
        for i in self._selectedPoints:
            self._outputSelectedPoints.append({'name' : i['name'],
                                               'discrete' : i['discrete'],
                                               'world' : i['world'],
                                               'value' : i['value']})

        # then make sure this structure knows that it has been modified
        self._outputSelectedPoints.notify()
        
#################################################################
# callbacks
#################################################################

    def _acs_nb_page_changed_cb(self, event):
        return 1
        nb = self._viewFrame.acsNotebook
        cur_panel = nb.GetPage(nb.GetSelection())
        if self._ipws[nb.GetSelection()].GetEnabled():
            cur_panel.enabledCbox.SetValue(true)
        else:
            cur_panel.enabledCbox.SetValue(false)

    def _ipwStartInteractionCallback(self, direction):
        self._viewFrame.acsNotebook.SetSelection(direction)
        self._ipwInteractionCallback(direction)

    def _ipwInteractionCallback(self, direction):
        cd = 4 * [0.0]
        if self._ipws[direction][0].GetCursorData(cd):
            nb = self._viewFrame.acsNotebook
            cur_panel = nb.GetPage(nb.GetSelection())
            self._current_cursors[direction] = cd
            cstring = str(cd[0:3]) + " = " + str(cd[3])
            cur_panel.cursorText.SetValue(cstring)

        # find the orthoView (if any) which tracks this IPW
        directionL = [v['direction'] for v in self._orthoViews
                      if v['direction'] == direction]
        
        if directionL:
            self._syncOrthoViewWithIPW(directionL[0])
            [self._viewFrame.ortho1RWI, self._viewFrame.ortho2RWI]\
                                        [directionL[0]].Render()

    def _ipwEndInteractionCallback(self, direction):
        self._syncOverlay(direction)
        self._ipwInteractionCallback(direction)

    def _pointWidgetInteractionCallback(self, pw, evt_name):
        # we have to find pw in our list
        pwidgets = map(lambda i: i['point_widget'], self._selectedPoints)
        if pw in pwidgets:
            idx = pwidgets.index(pw)
            # toggle the selection for this point in our list
            self._viewFrame.spointsGrid.SelectRow(idx)

            # get its position and transfer it to the sphere actor that
            # we use
            pos = pw.GetPosition()
            self._selectedPoints[idx]['sphere_actor'].SetPosition(pos)

            # also update the text_actor (if appropriate)
            ta = self._selectedPoints[idx]['text_actor']
            if ta:
                ta.SetPosition(pos)


            if self._ipws[0]:
                inputData = self._ipws[0][0].GetInput()
            else:
                inputData = None

            if inputData:
                # then we have to update our internal record of this point
                ispacing = inputData.GetSpacing()
                iorigin = inputData.GetOrigin()
                discrete = map(round,
                            map(operator.div,
                                map(operator.sub, pos, iorigin), ispacing))
                val = inputData.GetScalarComponentAsFloat(discrete[0],
                                                          discrete[1],
                                                          discrete[2], 0)
            else:
                discrete = (0, 0, 0)
                val = 0
                
            # the cursor is a tuple with discrete position and value
            self._selectedPoints[idx]['discrete'] = tuple(discrete)
            # 'world' is the world coordinates
            self._selectedPoints[idx]['world'] = tuple(pos)
            # and the value
            self._selectedPoints[idx]['value'] = val

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

    def _storeCursorCallback(self, i):
        """Call back for the store cursor button.

        Calls store cursor method on [x,y,z,v].
        """
        self._storeCursor(self._current_cursors[i])
        
    def voiWidgetInteractionCallback(self, o, e):
        planes = vtk.vtkPlanes()
        o.GetPlanes(planes)
        bounds =  planes.GetPoints().GetBounds()

        # first set bounds
        self._viewFrame.voiPanel.boundsText.SetValue(
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
        self._viewFrame.voiPanel.extentText.SetValue(
            "(%d %d %d %d %d %d)" % tuple(voi))


    def voiWidgetEndInteractionCallback(self, o, e):
        # adjust the vtkExtractVOI with the latest coords
        self._extractVOI.SetVOI(self._currentVOI)

    def inputModifiedCallback(self, o, e):
        # the data has changed, so re-render what's on the screen
        self._viewFrame.threedRWI.Render()

    def _rwiLeftButtonCallback(self, obj, event):

        def findPickedProp(obj):
            (x,y) = obj.GetEventPosition()
            picker = vtk.vtkPointPicker()
            picker.SetTolerance(0.005)
            picker.Pick(x,y,0.0,self._threedRenderer)
            return (picker.GetActor(), picker.GetPointId())
            
        pickAction = self._viewFrame.surfacePickActionRB.GetSelection()
        if pickAction == 1:
            # Place point on surface
            actor, pointId = findPickedProp(obj)
            if pointId >= 0 and actor:
                self._storeSurfacePoint(pointId, actor)
                
        elif pickAction == 2:
            # configure picked object
            prop, pointId = findPickedProp(obj)
            if prop:
                self.vtkPipelineConfigure(self._viewFrame,
                                          self._viewFrame.threedRWI, (prop,))

