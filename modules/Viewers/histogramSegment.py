from moduleBase import moduleBase
from moduleMixins import introspectModuleMixin
import moduleUtils
import vtk
import vtkdevide
import wx

class histogramSegment(introspectModuleMixin, moduleBase):
    """Mooooo!  I'm a cow.

    $Revision: 1.3 $
    """

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        self._createViewFrame()
        self._grid = self._viewFrame.selectorGrid

        self._buildPipeline()

        self._selectors = []

        self._bindEvents()     

        # display the window
        self._viewFrame.Show(True)
        

    def close(self):
        for i in range(len(self.getInputDescriptions())):
            self.setInput(i, None)

        # call close method of base class
        moduleBase.close(self)

        # we should be able to take care of our renderwindow now
        # we have to do this nasty trick until my Finalize changes are
        # implemented in all vtkRenderWindow types
        self._renderer.RemoveAllProps()
        del self._renderer
        self._viewFrame.rwi.GetRenderWindow().WindowRemap()
        self._viewFrame.Destroy()
        del self._viewFrame

    def getInputDescriptions(self):
        return ('Image Data 1', 'Imaga Data 2')

    def setInput(self, idx, inputStream):

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
            self._histogram.SetInput1(input0)

        elif idx == 1:
            input1 = checkTypeAndReturnInput(inputStream)
            self._histogram.SetInput2(input1)

        if self._histogram.GetInput(0) and self._histogram.GetInput(1):
            if self._ipw == None:
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
                self._ipw.SetUseContinuousCursor(1)
                # make sure the user can't twist the plane out of sight
                self._ipw.SetMiddleButtonAction(0)
                self._ipw.SetRightButtonAction(0)
                
                self._ipw.On()

                self._resetCamera()
                self._render()

        else:
            # this means at least one input is not valid
            if self._ipw != None:
                self._ipw.Off()
                self._ipw.SetInteractor(None)
                self._ipw.SetInput(None)
                self._ipw = None


    def getOutputDescriptions(self):
        return ('Segmented vtkImageData',)

    def getOutput(self, idx):
        return None

    def executeModule(self):
        pass

    def logicToConfig(self):
        pass
    
    def configToLogic(self):
        pass

    def viewToConfig(self):
        pass

    def configToView(self):
        pass

    def view(self):
        self._viewFrame.Show(True)
        self._viewFrame.Raise()
        

    # -------------------------------------------------------
    # END OF API METHODS
    # -------------------------------------------------------

    def _bindEvents(self):
        # fix the broken grid
        wx.grid.EVT_GRID_RANGE_SELECT(
            self._grid, self._handlerGridRangeSelect)

        wx.EVT_BUTTON(self._viewFrame, self._viewFrame.addButton.GetId(),
                      self._handlerAddSelector)

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

        moduleUtils.createStandardObjectAndPipelineIntrospection(
            self, self._viewFrame, self._viewFrame.viewFramePanel,
            {'Module (self)' : self,
             'vtkHistogram2D' : self._histogram,
             'vtkRenderer' : self._renderer},
            self._renderer.GetRenderWindow())

        # add the ECASH buttons
        moduleUtils.createECASButtons(self, self._viewFrame,
                                      self._viewFrame.viewFramePanel)
        

    def _createViewFrame(self):
        # create the viewerFrame
        import modules.Viewers.resources.python.histogramSegmentFrames

        viewFrame = modules.Viewers.resources.python.histogramSegmentFrames.\
                    viewFrame

        # DeVIDE takes care of the icon and the window close handlers
        self._viewFrame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager, viewFrame)
        

    def _handlerAddSelector(self, event):
        sw = vtk.vtkSplineWidget()
        sw.SetCurrentRenderer(self._renderer)
        sw.SetDefaultRenderer(self._renderer)
        sw.SetInput(self._histogram.GetOutput())
        sw.SetInteractor(self._viewFrame.rwi)
        sw.PlaceWidget()
        sw.ProjectToPlaneOn()
        sw.SetProjectionNormalToZAxes()
        sw.SetProjectionPosition(0.01)
        sw.SetPriority(0.6)
        sw.SetNumberOfHandles(4)
        sw.SetClosed(1)
        sw.On()
        self._selectors.append(sw)
        
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


    def _resetCamera(self):
        # make sure camera is cool
        cam = self._renderer.GetActiveCamera()
        cam.ParallelProjectionOn()
        self._renderer.ResetCamera()                
        ps = cam.GetParallelScale()
        # get the camera a tad closer than VTK default
        cam.SetParallelScale(ps / 2.9)

    def _render(self):
        self._renderer.GetRenderWindow().Render()

                
        
