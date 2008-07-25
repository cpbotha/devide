from module_base import ModuleBase
from moduleMixins import introspectModuleMixin
import module_utils
import vtk
import vtkdevide
import wx

class histogramSegment(introspectModuleMixin, ModuleBase):
    """Mooooo!  I'm a cow.

    $Revision: 1.9 $
    """

    _gridCols = [('Type', 0), ('Number of Handles',0)]
    _gridTypeCol = 0
    _gridNOHCol = 1
    

    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        self._createViewFrame()
        self._grid = self._viewFrame.selectorGrid

        self._buildPipeline()

        self._selectors = []
        self._config.selectorList = []
        self._initialiseGrid()

        self._bindEvents()

        # display the window
        self._viewFrame.Show(True)
        

    def close(self):
        for i in range(len(self.get_input_descriptions())):
            self.set_input(i, None)

        # call close method of base class
        ModuleBase.close(self)

        # we should be able to take care of our renderwindow now
        # we have to do this nasty trick until my Finalize changes are
        # implemented in all vtkRenderWindow types
        self._renderer.RemoveAllViewProps()
        del self._renderer
        self._viewFrame.rwi.GetRenderWindow().WindowRemap()
        self._viewFrame.Destroy()
        del self._viewFrame

    def get_config(self):
        return self._config

    def set_config(self, config):
        pass

    def set_configPostConnect(self, config):

        # first nuke all current selectors (but prevent updates to config
        # and the stencil)
        indices = range(len(self._selectors))
        self._removeSelector(indices, preventSync=True)

        for d in config.selectorList:
            self._addSelector(d['type'], len(d['handlePositions']))
            for hidx in range(len(d['handlePositions'])):
                self._selectors[-1]['widget'].SetHandlePosition(
                    hidx, d['handlePositions'][hidx])
            
        # we've now added all selectors, sync up everything!
        self._postSelectorChange()

    def get_input_descriptions(self):
        return ('Image Data 1', 'Imaga Data 2')

    def set_input(self, idx, inputStream):

        def checkTypeAndReturnInput(inputStream):
            """Check type of input.  None gets returned.  The input is
            returned if it has a valid type.  An exception is thrown if
            the input is invalid.
            """
            
            if inputStream == None:
                # disconnect
                return None
                
            else:
                # first check the type
                validType = False
                try:
                    if inputStream.IsA('vtkImageData'):
                        validType = True

                except AttributeError:
                    # validType is already False
                    pass

                if not validType:
                    raise TypeError, 'Input has to be of type vtkImageData.'
                else:
                    return inputStream
            
        if idx == 0:
            input0 = checkTypeAndReturnInput(inputStream)
            if input0 == None:
                # we HAVE to destroy the overlayipw first (the stencil
                # logic is NOT well-behaved)
                self._deactivateOverlayIPW()

            self._histogram.SetInput1(input0)
            self._lookupAppend.SetInput(0, input0)

        elif idx == 1:
            input1 = checkTypeAndReturnInput(inputStream)
            if input1 == None:
                # we HAVE to destroy the overlayipw first (the stencil
                # logic is NOT well-behaved)
                self._deactivateOverlayIPW()

            self._histogram.SetInput2(input1)
            if self._lookupAppend.GetNumberOfInputPorts() < 2:
                self._lookupAppend.AddInput(input1)
            else:
                self._lookupAppend.SetInput(1, input1)

        if self._histogram.GetInput(0) and self._histogram.GetInput(1):
            if self._ipw == None:
                self._createIPW()
                self._activateOverlayIPW()

        else:
            # this means at least one input is not valid - so we can disable
            # the primary IPW.  The overlay is dead by this time.
            if self._ipw != None:
                self._ipw.Off()
                self._ipw.SetInteractor(None)
                self._ipw.SetInput(None)
                self._ipw = None

                self._renderer.RemoveActor(self._axes)
                self._axes = None

                if 0:
                    # also disable scalarBarWidget
                    self._scalarBarWidget.Off()
                    self._scalarBarWidget.SetInteractor(None)
                    self._scalarBarWidget.GetScalarBarActor().SetLookupTable(
                        None)
                    self._scalarBarWidget = None

    def get_output_descriptions(self):
        return ('Segmented vtkImageData', 'Histogram Stencil')

    def get_output(self, idx):
        if idx == 0:
            return self._lookup.GetOutput()
        else:
            return self._stencil.GetOutput()

    def execute_module(self):
        pass

    def logic_to_config(self):
        pass
    
    def config_to_logic(self):
        pass

    def view_to_config(self):
        pass

    def config_to_view(self):
        pass

    def view(self):
        self._viewFrame.Show(True)
        self._viewFrame.Raise()
        

    # -------------------------------------------------------
    # END OF API METHODS
    # -------------------------------------------------------

    def _activateOverlayIPW(self):
        if self._overlayipw == None and \
           self._ipw and \
           self._histogram.GetInput(0) and \
           self._histogram.GetInput(1) and \
           len(self._selectors) > 0:

            # we only do this if absolutely necessary

            # connect these two up ONLY if we have valid selectors
            self._stencil.SetStencil(self._pdToImageStencil.GetOutput())

            self._overlayipw = vtk.vtkImagePlaneWidget()
            self._overlayipw.SetInput(self._stencil.GetOutput())
            self._stencil.GetOutput().Update()
            self._overlayipw.SetInput(self._stencil.GetOutput())
            self._overlayipw.SetInteractor(self._viewFrame.rwi)
            self._overlayipw.SetPlaneOrientation(2)
            self._overlayipw.SetSliceIndex(0)
            
            # build the lut
            lut = vtk.vtkLookupTable()
            lut.SetTableRange(0, 1)
            lut.SetHueRange(0.0, 0.0)
            lut.SetSaturationRange(1.0, 1.0)
            lut.SetValueRange(1.0, 1.0)
            lut.SetAlphaRange(0.0, 0.3)
            lut.Build()
            self._overlayipw.SetUserControlledLookupTable(1)
            self._overlayipw.SetLookupTable(lut)
            
            self._overlayipw.On()
            self._overlayipw.InteractionOff()

            self._render()

    def _deactivateOverlayIPW(self):
        if self._overlayipw:
            print "switching off overlayipw"
            self._overlayipw.Off()
            self._overlayipw.SetInteractor(None)
            self._overlayipw.SetInput(None)
            self._overlayipw = None

            print "disconnecting stencil"
            # also disconnect this guy, or we crash!
            self._stencil.SetStencil(None)

            
            

    def _addSelector(self, selectorType, numPoints):
        if selectorType == 'Spline':
            sw = vtk.vtkSplineWidget()
        else:
            sw = vtkdevide.vtkPolyLineWidget()
            
        sw.SetCurrentRenderer(self._renderer)
        sw.SetDefaultRenderer(self._renderer)
        sw.SetInput(self._histogram.GetOutput())
        sw.SetInteractor(self._viewFrame.rwi)
        sw.PlaceWidget()
        sw.ProjectToPlaneOn()
        sw.SetProjectionNormalToZAxes()
        sw.SetProjectionPosition(0.00)
        sw.SetPriority(0.6)
        sw.SetNumberOfHandles(numPoints)
        sw.SetClosed(1)
        sw.On()

        swPolyData = vtk.vtkPolyData()
        self._selectors.append({'type' : selectorType,
                                'widget' : sw,
                                'polyData' : swPolyData})
        # add it to the appendPd
        self._appendPD.AddInput(swPolyData)
        nrGridRows = self._grid.GetNumberRows()
        self._grid.AppendRows()
        self._grid.SetCellValue(nrGridRows, self._gridTypeCol, selectorType)
        self._grid.SetCellValue(nrGridRows, self._gridNOHCol,
                                str(sw.GetNumberOfHandles()))

        self._postSelectorChange()

        sw.AddObserver('EndInteractionEvent',
                       self._observerSelectorEndInteraction)

        # make sure this is on
        self._activateOverlayIPW()

    def _bindEvents(self):
        # fix the broken grid
        wx.grid.EVT_GRID_RANGE_SELECT(
            self._grid, self._handlerGridRangeSelect)

        wx.EVT_BUTTON(self._viewFrame, self._viewFrame.addButton.GetId(),
                      self._handlerAddSelector)

        wx.EVT_BUTTON(self._viewFrame, self._viewFrame.removeButton.GetId(),
                      self._handlerRemoveSelector)

        wx.EVT_BUTTON(self._viewFrame,
                      self._viewFrame.changeHandlesButton.GetId(),
                      self._handlerChangeNumberOfHandles)

    def _buildPipeline(self):
        """Build underlying pipeline and configure rest of pipeline-dependent
        UI. 
        """
        
        # add the renderer
        self._renderer = vtk.vtkRenderer()
        self._renderer.SetBackground(0.5, 0.5, 0.5)
        self._viewFrame.rwi.GetRenderWindow().AddRenderer(
            self._renderer)
 
        self._histogram = vtkdevide.vtkImageHistogram2D()

        # make sure the user can't do anything entirely stupid
        istyle = vtk.vtkInteractorStyleImage()
        self._viewFrame.rwi.SetInteractorStyle(istyle)

        # we'll use this to keep track of our ImagePlaneWidget
        self._ipw = None
        self._overlayipw = None
        self._scalarBarWidget = None

        #
        self._appendPD = vtk.vtkAppendPolyData()

        self._extrude = vtk.vtkLinearExtrusionFilter()
        self._extrude.SetInput(self._appendPD.GetOutput())
        self._extrude.SetScaleFactor(1)
        self._extrude.SetExtrusionTypeToNormalExtrusion()
        self._extrude.SetVector(0,0,1)

        self._pdToImageStencil = vtk.vtkPolyDataToImageStencil()
        self._pdToImageStencil.SetInput(self._extrude.GetOutput())

        # stupid trick to make image with all ones, but as large as its
        # input
        
        self._allOnes = vtk.vtkImageThreshold()
        self._allOnes.ThresholdByLower(0.0)
        self._allOnes.ThresholdByUpper(0.0)
        self._allOnes.SetInValue(1.0)
        self._allOnes.SetOutValue(1.0)
        self._allOnes.SetInput(self._histogram.GetOutput())

        self._stencil = vtk.vtkImageStencil()
        self._stencil.SetInput(self._allOnes.GetOutput())
        #self._stencil.SetStencil(self._pdToImageStencil.GetOutput())
        self._stencil.ReverseStencilOff()
        self._stencil.SetBackgroundValue(0)

        self._lookupAppend = vtk.vtkImageAppendComponents()

        self._lookup = vtkdevide.vtkHistogramLookupTable()
        self._lookup.SetInput1(self._lookupAppend.GetOutput())        
        self._lookup.SetInput2(self._stencil.GetOutput())

        module_utils.createStandardObjectAndPipelineIntrospection(
            self, self._viewFrame, self._viewFrame.viewFramePanel,
            {'Module (self)' : self,
             'vtkHistogram2D' : self._histogram,
             'vtkRenderer' : self._renderer},
            self._renderer.GetRenderWindow())

        # add the ECASH buttons
        module_utils.createECASButtons(self, self._viewFrame,
                                      self._viewFrame.viewFramePanel)

    def _createIPW(self):
        # we have to do this to get the correct log range
        self._histogram.GetOutput().Update()
        
        # this means we have newly valid input and should setup an ipw
        self._ipw = vtk.vtkImagePlaneWidget()
        self._histogram.GetOutput().Update()
        self._ipw.SetInput(self._histogram.GetOutput())
        self._ipw.SetInteractor(self._viewFrame.rwi)
        # normal to the Z-axis
        self._ipw.SetPlaneOrientation(2)
        self._ipw.SetSliceIndex(0)

        # setup specific lut
        srange = self._histogram.GetOutput().GetScalarRange()
        lut = vtk.vtkLookupTable()
        lut.SetScaleToLog10()                
        lut.SetTableRange(srange)
        lut.SetSaturationRange(1.0,1.0)
        lut.SetValueRange(1.0, 1.0)
        lut.SetHueRange(0.1, 1.0)
        lut.Build()
        self._ipw.SetUserControlledLookupTable(1)
        self._ipw.SetLookupTable(lut)
        
        self._ipw.SetDisplayText(1)
        # if we use ContinousCursor, we get OffImage when zoomed
        # on Linux (really irritating) but not on Windows.  A VTK
        # recompile might help, we'll see.
        self._ipw.SetUseContinuousCursor(1)
        # make sure the user can't twist the plane out of sight
        self._ipw.SetMiddleButtonAction(0)
        self._ipw.SetRightButtonAction(0)

        # add an observer
        self._ipw.AddObserver('StartInteractionEvent',
                              self._observerIPWInteraction)
        self._ipw.AddObserver('InteractionEvent',
                              self._observerIPWInteraction)
        self._ipw.AddObserver('EndInteractionEvent',
                              self._observerIPWInteraction)
        
        self._ipw.On()

        self._axes = vtk.vtkCubeAxesActor2D()
        self._axes.SetFlyModeToOuterEdges()
        # NOBODY will ever know why we have to switch off the Y axis when
        # we actually want the Z-axis to go away.
        self._axes.YAxisVisibilityOff()
        self._axes.SetBounds(self._ipw.GetResliceOutput().GetBounds())
        
        self._renderer.AddActor(self._axes)
        self._axes.SetCamera(self._renderer.GetActiveCamera())
        self._axes.PickableOff()

        if 0:
            # now add a scalarbar
            self._scalarBarWidget = vtk.vtkScalarBarWidget()
            self._scalarBarWidget.SetInteractor(self._viewFrame.rwi)
            self._scalarBarWidget.GetScalarBarActor().SetTitle('Frequency')
            self._scalarBarWidget.GetScalarBarActor().SetLookupTable(
                lut)
            # and activate
            self._scalarBarWidget.On()
        
        self._resetCamera()
        self._render()
        

    def _createViewFrame(self):
        # create the viewerFrame
        import modules.viewers.resources.python.histogramSegmentFrames
        # this reload is temporary during development
        reload(modules.viewers.resources.python.histogramSegmentFrames)

        viewFrame = modules.viewers.resources.python.histogramSegmentFrames.\
                    viewFrame

        # DeVIDE takes care of the icon and the window close handlers
        self._viewFrame = module_utils.instantiateModuleViewFrame(
            self, self._module_manager, viewFrame)
        

    def _handlerAddSelector(self, event):
        typeString = self._viewFrame.selectorTypeChoice.GetStringSelection()
        self._addSelector(typeString, 5)

    def _handlerChangeNumberOfHandles(self, event):
        # first check that the user has actually selected something we
        # can work with...
        selectedRows = self._grid.GetSelectedRows()
        if len(selectedRows) == 0:
            return
        
        nohText = wx.GetTextFromUser(
            'Enter a new number of handles > 2 for all selected selectors.')

        if nohText:
            try:
                nohInt = int(nohText)
            except ValueError:
                pass
            else:
                if nohInt < 2:
                    nohInt = 2

                for row in selectedRows:
                    self._selectors[row]['widget'].SetNumberOfHandles(nohInt)
                    self._grid.SetCellValue(row, self._gridNOHCol,
                                            str(nohInt))

                # we've made changes to the selectors, so we have to
                # notify the stencil.... (and other stuff)
                self._postSelectorChange()
                
    def _observerIPWInteraction(self, e, o):
        if not self._ipw:
            return
        
        cd = 4 * [0.0]
        if self._ipw.GetCursorData(cd):
            if 0:
                # get world position (at least for first two coords)
                inp = self._ipw.GetInput()
                spacing = inp.GetSpacing()
                origin = inp.GetOrigin()
                # calculate origin + spacing * discrete (only if we're getting
                # discrete values from the IPW, which we aren't)
                temp = [s * d for s,d in zip(spacing, cd[0:3])]
                w = [o + t for o,t in zip(origin,temp)]
                #
                
            self._viewFrame.cursorValuesText.SetValue(
                '%.2f, %.2f == %d' % (cd[0], cd[1], int(cd[3])))
            

    def _handlerRemoveSelector(self, event):
        selectedRows = self._grid.GetSelectedRows()
        if len(selectedRows) > 0:
            self._removeSelector(selectedRows)
            # after that, we have to sync
            self._postSelectorChange()
            self._render()
        
    def _handlerGridRangeSelect(self, event):
        """This event handler is a fix for the fact that the row
        selection in the wxGrid is deliberately broken.  It's also
        used to activate and deactivate relevant menubar items.
        
        Whenever a user clicks on a cell, the grid SHOWS its row
        to be selected, but GetSelectedRows() doesn't think so.
        This event handler will travel through the Selected Blocks
        and make sure the correct rows are actually selected.
        
        Strangely enough, this event always gets called, but the
        selection is empty when the user has EXPLICITLY selected
        rows.  This is not a problem, as then the GetSelectedRows()
        does return the correct information.
        """

        # both of these are lists of (row, column) tuples
        tl = self._grid.GetSelectionBlockTopLeft()
        br = self._grid.GetSelectionBlockBottomRight()

        # this means that the user has most probably clicked on the little
        # block at the top-left corner of the grid... in this case,
        # SelectRow has no frikking effect (up to wxPython 2.4.2.4) so we
        # detect this situation and clear the selection (we're going to be
        # selecting the whole grid in anycase.
        if tl == [(0,0)] and br == [(self._grid.GetNumberRows() - 1,
                                     self._grid.GetNumberCols() - 1)]:
            self._grid.ClearSelection()

        for (tlrow, tlcolumn), (brrow, brcolumn) in zip(tl, br):
            for row in range(tlrow,brrow + 1):
                self._grid.SelectRow(row, True)

    def _initialiseGrid(self):
        # delete all existing columns
        self._grid.DeleteCols(0, self._grid.GetNumberCols())

        # we need at least one row, else adding columns doesn't work (doh)
        self._grid.AppendRows()
        
        # setup columns
        self._grid.AppendCols(len(self._gridCols))
        for colIdx in range(len(self._gridCols)):
            # add labels
            self._grid.SetColLabelValue(colIdx, self._gridCols[colIdx][0])

        # set size according to labels
        self._grid.AutoSizeColumns()

        for colIdx in range(len(self._gridCols)):
            # now set size overrides
            size = self._gridCols[colIdx][1]
            if size > 0:
                self._grid.SetColSize(colIdx, size)

        # make sure we have no rows again...
        self._grid.DeleteRows(0, self._grid.GetNumberRows())

    def _observerSelectorEndInteraction(self, obj, evt):
        # we don't HAVE to do this immediately, but it's fun
        self._postSelectorChange()

    def _postSelectorChange(self):
        self._syncStencilMask()
        self._syncConfigWithSelectors()

    def _removeSelector(self, indices, preventSync=False):
        if indices:
            # we have to delete these things from behind (he he he)
            indices.sort()
            indices.reverse()
            for idx in indices:
                # take care of the selector
                w = self._selectors[idx]['widget']
                wpd = self._selectors[idx]['polyData']
                w.Off()
                w.SetInteractor(None)
                w.SetInput(None)
                self._appendPD.RemoveInput(wpd)
                del(self._selectors[idx])
                # reflect the removal in the grid
                self._grid.DeleteRows(idx, 1)

        if len(self._selectors) == 0:
            self._deactivateOverlayIPW()

        if not preventSync:
            # sometimes, we don't want this to be called, as it will cause
            # unnecessary updates, for example when we nuke ALL selectors
            # during a set_config
            self._postSelectorChange()
        
    def _render(self):
        self._renderer.GetRenderWindow().Render()


    def _resetCamera(self):
        # make sure camera is cool
        cam = self._renderer.GetActiveCamera()
        cam.ParallelProjectionOn()
        self._renderer.ResetCamera()                
        ps = cam.GetParallelScale()
        # get the camera a tad closer than VTK default
        cam.SetParallelScale(ps / 2.9)

    def _syncStencilMask(self):
        for d in self._selectors:
            sw = d['widget']
            spd = d['polyData']
            # transfer polydata
            sw.GetPolyData(spd)

        if self._overlayipw:
            # the stencil is a bitch - we have to be very careful about when
            # we talk to it...
            self._stencil.Update()

    def _syncConfigWithSelectors(self):
        # we could get the data from the selector polydata, but we'll rather
        # get it from the handles, because that's ultimately how we'll
        # restore it again

        del self._config.selectorList[:]

        
        for d in self._selectors:
            handlePositions = []
            widget = d['widget']
            for hidx in range(widget.GetNumberOfHandles()):
                # it's important that we create a new var everytime
                thp = [0.0, 0.0, 0.0]                
                widget.GetHandlePosition(hidx, thp)
                handlePositions.append(thp)

            self._config.selectorList.append(
                {'type' : d['type'],
                 'handlePositions' : handlePositions})
        

        
                
        
