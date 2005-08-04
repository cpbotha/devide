# sliceDirection.py copyright (c) 2003 Charl P. Botha <cpbotha@ieee.org>
# $Id: sliceDirection.py,v 1.24 2005/08/04 16:23:31 cpbotha Exp $
# does all the actual work for a single slice in the slice3dVWR

import operator
import moduleUtils
import vtk
import wx

class sliceDirection:
    """Class encapsulating all logic behind a single direction.

    This class contains the IPWs and related paraphernalia for all layers
    (primary + overlays) representing a single view direction.  It optionally
    has its own window with an orthogonal view.
    """

    overlayModes = {'Green Fusion' : 'greenFusion',
                    'Red Fusion' : 'redFusion',
                    'Blue Fusion' : 'blueFusion',
                    'Hue Fusion' : 'hueFusion',
                    'Hue/Value Fusion' : 'hueValueFusion',
                    'Green Opacity Range' : 'greenOpacityRange',
                    'Red Opacity Range' : 'redOpacityRange',
                    'Blue Opacity Range' : 'blueOpacityRange',
                    'Hue Opacity Range' : 'hueOpacityRange',
                    'Primary LUT fusion' : 'primaryLUTFusion'}

    def __init__(self, name, sliceDirections, defaultPlaneOrientation=2):
        self.sliceDirections = sliceDirections
        self._defaultPlaneOrientation = 2

        # orthoPipeline is a list of dictionaries.  each dictionary is:
        # {'planeSource' : vtkPlaneSource, 'planeActor' : vtkActor,
        #  'textureMapToPlane' : vtkTextureMapToPlane,
        #  '
        self._orthoPipeline = []
        # this is the frame that we will use to display our slice pipeline
        self._orthoViewFrame = None
        #
        self._renderer = None

        # list of vtkImagePlaneWidgets (first is "primary", rest are overlays)
        self._ipws = []

        # then some state variables
        self._enabled = True
        self._interactionEnabled = True

        # list of objects that want to be contoured by this slice
        self._contourObjectsDict = {}

        self.overlayMode = 'greenOpacityRange'
        self.fusionAlpha = 0.4

        # we'll use this to store the polydata of our primary slice
        self._primaryCopyPlaneSource = vtk.vtkPlaneSource()
        self._primaryCopyPlaneSource.SetXResolution(64)
        self._primaryCopyPlaneSource.SetYResolution(64)
        self.primaryPolyData = self._primaryCopyPlaneSource.GetOutput()

    def addContourObject(self, contourObject, prop3D):
        """Activate contouring for the contourObject.  The contourObject
        is usually a tdObject and specifically a vtkPolyData.  We also
        need the prop3D that represents this polydata in the 3d scene.
        """
        if self._contourObjectsDict.has_key(contourObject):
            # we already have this, thanks
            return

        try:
            contourable = contourObject.IsA('vtkPolyData')
        except:
            contourable = False

        if contourable:
            # we need a cutter to calculate the contours and then a stripper
            # to string them all together
            cutter = vtk.vtkCutter()
            plane = vtk.vtkPlane()
            cutter.SetCutFunction(plane)
            trfm = vtk.vtkTransform()
            trfm.SetMatrix(prop3D.GetMatrix())
            trfmFilter = vtk.vtkTransformPolyDataFilter()
            trfmFilter.SetTransform(trfm)
            trfmFilter.SetInput(contourObject)
            cutter.SetInput(trfmFilter.GetOutput())
            stripper = vtk.vtkStripper()
            stripper.SetInput(cutter.GetOutput())
            
            #
            tubef = vtk.vtkTubeFilter()
            tubef.SetNumberOfSides(12)
            tubef.SetRadius(0.5)
            tubef.SetInput(stripper.GetOutput())

            # and create the overlay at least for the 3d renderer
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInput(tubef.GetOutput())
            mapper.ScalarVisibilityOff()
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            c = self.sliceDirections.slice3dVWR._tdObjects.getObjectColour(
                contourObject)
            actor.GetProperty().SetColor(c)
            actor.GetProperty().SetInterpolationToFlat()

            # add it to the renderer
            self.sliceDirections.slice3dVWR._threedRenderer.AddActor(actor)
            
            # add all necessary metadata to our dict
            contourDict = {'contourObject' : contourObject,
                           'contourObjectProp' : prop3D,
                           'trfmFilter' : trfmFilter,
                           'cutter' : cutter,
                           'tdActor' : actor}
                           
            self._contourObjectsDict[contourObject] = contourDict

            # now sync the bugger
            self.syncContourToObject(contourObject)

    def addAllContourObjects(self):
        cos = self.sliceDirections.slice3dVWR._tdObjects.getContourObjects()
        for co in cos:
            prop = self.sliceDirections.slice3dVWR._tdObjects.\
                   findPropByObject(co)
            # addContourObject is clever enough not to try and add contours
            # for objects which aren't contourable
            self.addContourObject(co, prop)

    def removeAllContourObjects(self):
        contourObjects = self._contourObjectsDict.keys()
        for co in contourObjects:
            self.removeContourObject(co)

    def removeContourObject(self, contourObject):
        if contourObject in self._contourObjectsDict:
            # let's remove it from the renderer
            actor  = self._contourObjectsDict[contourObject]['tdActor']
            self.sliceDirections.slice3dVWR._threedRenderer.RemoveActor(actor)
            # and remove it from the dict
            del self._contourObjectsDict[contourObject]

    def syncContourToObjectViaProp(self, prop):
        for coi in self._contourObjectsDict.items():
            if coi[1]['contourObjectProp'] == prop:
                # there can be only one (and contourObject is the key)
                self.syncContourToObject(coi[0])
                # break out of the innermost loop
                break
        
    def syncContourToObject(self, contourObject):
        """Update the contour for the given contourObject.  contourObject
        corresponds to a tdObject in tdObjects.py.
        """
        # yes, in and not in work on dicts, doh
        if contourObject not in self._contourObjectsDict:
            return

        # if there are no ipws, we have no planes!
        if not self._ipws:
            return

        # get the contourObject metadata
        contourDict = self._contourObjectsDict[contourObject]
        cutter = contourDict['cutter']
        plane = cutter.GetCutFunction()

        # adjust the implicit plane (if we got this far (i.e.
        normal = self._ipws[0].GetNormal()
        origin = self._ipws[0].GetOrigin()
        plane.SetNormal(normal)
        plane.SetOrigin(origin)

        # also make sure the transform knows about the new object position
        contourDict['trfmFilter'].GetTransform().SetMatrix(
            contourDict['contourObjectProp'].GetMatrix())
        
        # calculate it
        cutter.Update()
        
    def addData(self, inputData):
        """Add inputData as a new layer.
        """
        
        if inputData is None:
            raise Exception, "Hallo, the inputData is none.  Doing nothing."

        # make sure it's vtkImageData
        if hasattr(inputData, 'IsA') and inputData.IsA('vtkImageData'):
        
            # if we already have this data as input, we can't take it
            for ipw in self._ipws:
                if inputData is ipw.GetInput():
                    raise Exception,\
                          "This inputData already exists in this slice."

            # make sure it's all up to date
            inputData.Update()

            if self._ipws:
                # this means we already have data and what's added now can
                # only be allowed as overlay

                # now check if the new data classifies as overlay
                mainInput = self._ipws[0].GetInput()

                if inputData.GetWholeExtent() != mainInput.GetWholeExtent():
                    raise Exception, \
                          "The extent of this inputData " \
                          "does not match the extent of the existing input" \
                          ", so it can't be used as overlay:\n"\
                          "[%s != %s]" % \
                          (inputData.GetWholeExtent(),
                           mainInput.GetWholeExtent())


                # differences in spacing between new input and existing input
                spacingDiff = [abs(i - j) for (i,j) in
                               zip(inputData.GetSpacing(),
                                   mainInput.GetSpacing())]
                # maximal allowable difference
                spacingEpsilon = 0.0001                

                if spacingDiff[0] > spacingEpsilon or \
                   spacingDiff[1] > spacingEpsilon or \
                   spacingDiff[2] > spacingEpsilon:
                    raise Exception, \
                          "The spacing of this inputData " \
                          "does not match the spacing of the existing input" \
                          ", so it can't be used as overlay.\n"\
                          "[%s != %s]" % \
                          (inputData.GetSpacing(),
                           mainInput.GetSpacing())
                
                self._ipws.append(vtk.vtkImagePlaneWidget())
                self._ipws[-1].SetInput(inputData)
                self._ipws[-1].UserControlledLookupTableOn()
                self._ipws[-1].SetResliceInterpolateToNearestNeighbour()
                
                # now make sure they have the right lut and are synched
                # with the main IPW
                self._resetOverlays()

                if self._orthoViewFrame:
                    # also update our orthoView
                    self._createOrthoPipelineForNewIPW(self._ipws[-1])
                    self._syncOrthoView()
                    self._orthoViewFrame.RWI.Render()
                
            # if self._ipws ...
            else:
                # this means primary data!

                self._ipws.append(vtk.vtkImagePlaneWidget())
                #self._ipws[-1].GetPolyDataAlgorithm().SetXResolution(64)
                #self._ipws[-1].GetPolyDataAlgorithm().SetYResolution(64)
                
                self._ipws[-1].SetInput(inputData)
                self._ipws[-1].SetPicker(self.sliceDirections.ipwPicker)
                # GetColorMap() -- new VTK CVS
                self._ipws[-1].GetColorMap().SetOutputFormatToRGB()
                #self._ipws[-1].GetImageMapToColors().SetOutputFormatToRGB()

                # now make callback for the ipw
                self._ipws[-1].AddObserver('StartInteractionEvent',
                                lambda e, o:
                                self._ipwStartInteractionCallback())
                self._ipws[-1].AddObserver('InteractionEvent',
                                lambda e, o:
                                self._ipwInteractionCallback())
                self._ipws[-1].AddObserver('EndInteractionEvent',
                                lambda e, o:
                                self._ipwEndInteractionCallback())

                self._resetPrimary()

                # now let's update our orthoView as well (if applicable)
                if self._orthoViewFrame:
                    self._createOrthoPipelineForNewIPW(self._ipws[-1])
                    # and because it's a primary, we have to reset as well
                    # self._resetOrthoView() also calls self.SyncOrthoView()
                    self._resetOrthoView()
                    self._orthoViewFrame.Render()

                # also check for contourObjects (primary data is being added)
                self.addAllContourObjects()

                # make sure our output polydata is in sync with the new prim
                self._syncOutputPolyData()

                # first we name ourselves... (ImageReslice loses the input
                # scalars name)
                rsoPD = self._ipws[-1].GetResliceOutput().GetPointData()
                rsoScalars = rsoPD.GetScalars()

                if rsoScalars:
                    if rsoScalars.GetName():
                        print "sliceDirection.py: WARNING - ResliceOutput " \
                        "scalars are named."
                    else:
                        rsoScalars.SetName('ipw_reslice_output')
                
                # and add ourselvess to the output unstructured grid pointer
                self.sliceDirections.ipwAppendFilter.AddInput(
                    self._ipws[-1].GetResliceOutput())

    def close(self):
        """Shut down everything."""

        # take out all the contours
        self.removeAllContourObjects()
        
        # take out the orthoView
        self.destroyOrthoView()

        # first take care of all our ipws
        inputDatas = [i.GetInput() for i in self._ipws]
        for inputData in inputDatas:
            self.removeData(inputData)

        # kill the whole list
        del self._ipws

        # make sure we don't point to our sliceDirections
        del self.sliceDirections
        

    def createOrthoView(self):
        """Create an accompanying orthographic view of the sliceDirection
        encapsulated by this object.
        """

        # there can be only one orthoPipeline
        if not self._orthoPipeline:

            import modules.resources.python.slice3dVWRFrames            
            # import our wxGlade-generated frame
            ovf = modules.resources.python.slice3dVWRFrames.orthoViewFrame
            self._orthoViewFrame = ovf(
                self.sliceDirections.slice3dVWR.threedFrame, id=-1,
                title='dummy')

            self._orthoViewFrame.SetIcon(moduleUtils.getModuleIcon())

            self._renderer = vtk.vtkRenderer()
            self._renderer.SetBackground(0.5, 0.5, 0.5)
            self._orthoViewFrame.RWI.GetRenderWindow().AddRenderer(
                self._renderer)
            istyle = vtk.vtkInteractorStyleImage()
            self._orthoViewFrame.RWI.SetInteractorStyle(istyle)

            wx.EVT_CLOSE(self._orthoViewFrame,
                         lambda e, s=self: s.destroyOrthoView)

            wx.EVT_BUTTON(self._orthoViewFrame,
                          self._orthoViewFrame.closeButtonId,
                          lambda e, s=self: s.destroyOrthoView)

            for ipw in self._ipws:
                self._createOrthoPipelineForNewIPW(ipw)

            if self._ipws:
                self._resetOrthoView()

            self._orthoViewFrame.Show(True)

    def destroyOrthoView(self):
        """Destroy the orthoView and disconnect everything associated
        with it.
        """

        if self._orthoViewFrame:
            for layer in self._orthoPipeline:
                self._renderer.RemoveActor(layer['planeActor'])
                # this will disconnect the texture (it will destruct shortly)
                layer['planeActor'].SetTexture(None)

                # this should take care of all references
                layer = []

            self._orthoPipeline = []

            # remove our binding to the renderer
            self._renderer = None
            # remap the RenderWindow (it will create its own new window and
            # disappear when we remove our binding to the viewFrame)
            self._orthoViewFrame.RWI.GetRenderWindow().WindowRemap()

            # finally take care of the GUI
            self._orthoViewFrame.Destroy()
            # and take care to remove our viewFrame binding
            self._orthoViewFrame = None
        

    def enable(self):
        """Switch this sliceDirection on."""
        self._enabled = True
        for ipw in self._ipws:
            ipw.On()

        # alse re-enable all contours for this slice
        for (contourObject, contourDict) in self._contourObjectsDict.items():
            contourDict['tdActor'].VisibilityOn()

    def enableInteraction(self):
        self._interactionEnabled = True
        if self._ipws:
            self._ipws[0].SetInteraction(1)

    def disable(self):
        """Switch this sliceDirection off."""
        self._enabled = False
        for ipw in self._ipws:
            ipw.Off()

        # alse disable all contours for this slice
        for (contourObject, contourDict) in self._contourObjectsDict.items():
            contourDict['tdActor'].VisibilityOff()

    def disableInteraction(self):
        self._interactionEnabled = False
        if self._ipws:
            self._ipws[0].SetInteraction(0)

    def getEnabled(self):
        return self._enabled
    
    def getInteractionEnabled(self):
        return self._interactionEnabled

    def getOrthoViewEnabled(self):
        return self._orthoViewFrame is not None

    def getNumberOfLayers(self):
        return len(self._ipws)

    def lockToPoints(self, p0, p1, p2):
        """Make the plane co-planar with the plane defined by the three points.
        """

        if not self._ipws:
            # we can't do anything if we don't have a primary IPW
            return

        # we pick p0 as the origin
        p1o = map(operator.sub, p1, p0)
        p2o = map(operator.sub, p2, p0)
        planeNormal = [0,0,0]
        vtk.vtkMath.Cross(p1o, p2o, planeNormal)
        pnSize = vtk.vtkMath.Normalize(planeNormal)

        if pnSize > 0:
            try:
                planeSource = self._ipws[0].GetPolyDataAlgorithm()
            except AttributeError:
                planeSource = self._ipws[0].GetPolyDataSource()
                
            planeSource.SetNormal(planeNormal)
            planeSource.SetCenter(p0)
            self._ipws[0].UpdatePlacement()
            self._syncAllToPrimary()

        else:
            wx.wxLogMessage("The points you have chosen don't uniquely "
                            "define a plane.  Please try again.")

    def pushSlice(self, val):
        if self._ipws:
            try:
                planeSource = self._ipws[0].GetPolyDataAlgorithm()
            except AttributeError:
                planeSource = self._ipws[0].GetPolyDataSource()

            planeSource.Push(val)
            self._ipws[0].UpdatePlacement()
            self._syncAllToPrimary()

    def removeData(self, inputData):
        # search for the ipw with this inputData
        ipwL = [i for i in self._ipws if i.GetInput() is inputData]
        if ipwL:
            # there can be only one!
            ipw = ipwL[0]

            # switch it off
            ipw.Off()
            # disconnect it from the RWI
            ipw.SetInteractor(None)

            # we always try removing the input from the appendfilter
            self.sliceDirections.ipwAppendFilter.RemoveInput(
                ipw.GetResliceOutput())
            
            # disconnect the input
            ipw.SetInput(None)

            # finally delete our reference
            idx = self._ipws.index(ipw)            
            del self._ipws[idx]


        if not self._ipws:
            # if there is no data left, we also have to remove all contours
            self.removeAllContourObjects()

    def resetToACS(self, acs):
        """Reset the current sliceDirection to Axial, Coronal or Sagittal.
        """

        # colours of imageplanes; we will use these as keys
        ipw_cols = [(1,0,0), (0,1,0), (0,0,1)]

        orientation = 2 - acs
        for ipw in self._ipws:
            # this becomes the new default for resets as well
            self._defaultPlaneOrientation = orientation 
            ipw.SetPlaneOrientation(orientation)
            ipw.GetPlaneProperty().SetColor(ipw_cols[orientation])

        self._syncAllToPrimary()


    def _createOrthoPipelineForNewIPW(self, ipw):
        """This will create and append all the necessary constructs for a
        single new layer (ipw) to the self._orthoPipeline.

        Make sure you only call this method if the orthoView exists!
        After having done this, you still need to call _syncOrthoView() or
        _resetOrthoView() if you've added a new primary.
        """

        _ps = vtk.vtkPlaneSource()
        _pa = vtk.vtkActor()
        _tm2p = vtk.vtkTextureMapToPlane()
        self._orthoPipeline.append(
            {'planeSource' : _ps,
             'planeActor' : _pa,
             'textureMapToPlane': _tm2p})

        _tm2p.AutomaticPlaneGenerationOff()
        _tm2p.SetInput(_ps.GetOutput())
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInput(_tm2p.GetOutput())
        _pa.SetMapper(mapper)

        otherTexture = ipw.GetTexture()

        # we don't just use the texture, else VTK goes mad re-uploading
        # the same texture unnecessarily... let's just make use of the
        # same input, we get much more effective use of the
        # host->GPU bus
        texture = vtk.vtkTexture()
        texture.SetInterpolate(otherTexture.GetInterpolate())
        texture.SetQuality(otherTexture.GetQuality())
        texture.MapColorScalarsThroughLookupTableOff()
        texture.RepeatOff()
        texture.SetInput(otherTexture.GetInput())

        _pa.SetTexture(texture)

        self._renderer.AddActor(_pa)
        

    def _resetOverlays(self):
        """Rest all overlays with default LUT, plane orientation and
        start position."""

        if len(self._ipws) > 1:
            # iterate through overlay layers
            for ipw in self._ipws[1:]:
                lut = vtk.vtkLookupTable()                
                ipw.SetLookupTable(lut)
                self._setOverlayLookupTable(ipw)

                ipw.SetInteractor(
                    self.sliceDirections.slice3dVWR.threedFrame.threedRWI)
                # default axial orientation
                ipw.SetPlaneOrientation(self._defaultPlaneOrientation)
                ipw.SetSliceIndex(0)
                
                ipw.On()
                ipw.InteractionOff()

        self._syncOverlays()

    def _resetOrthoView(self):
        """Calling this will reset the orthogonal camera and bring us in
        synchronisation with the primary and overlays.
        """

        if self._orthoPipeline and self._ipws:
            self._syncOrthoView()
            # just get the first planesource
            planeSource = self._orthoPipeline[0]['planeSource']
            # let's setup the camera
            icam = self._renderer.GetActiveCamera()
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
        

    def _resetPrimary(self):
        """Reset primary layer.
        """

        if self._ipws:

            inputData = self._ipws[0].GetInput()
            
            # first make sure that the WHOLE primary will get updated
            # when we render, else we get stupid single slice renderings!
            inputData.UpdateInformation()
            inputData.SetUpdateExtentToWholeExtent()
            inputData.Update()
            
            # calculate default window/level once (same as used
            # by vtkImagePlaneWidget)
            (dmin,dmax) = inputData.GetScalarRange()
            iwindow = dmax - dmin
            ilevel = 0.5 * (dmin + dmax)

            inputData_source = inputData.GetSource()
            if hasattr(inputData_source, 'GetWindowCenter') and \
                   callable(inputData_source.GetWindowCenter):
                level = inputData_source.GetWindowCenter()
            else:
                level = ilevel

            if hasattr(inputData_source, 'GetWindowWidth') and \
                   callable(inputData_source.GetWindowWidth):
                window = inputData_source.GetWindowWidth()
            else:
                window = iwindow

            # colours of imageplanes; we will use these as keys
            ipw_cols = [(1,0,0), (0,1,0), (0,0,1)]

            ipw = self._ipws[0]
            ipw.DisplayTextOn()
            ipw.SetInteractor(
                self.sliceDirections.slice3dVWR.threedFrame.threedRWI)
            ipw.SetPlaneOrientation(self._defaultPlaneOrientation)
            ipw.SetSliceIndex(0)
            ipw.GetPlaneProperty().SetColor(
                ipw_cols[ipw.GetPlaneOrientation()])
            # set the window and level
            ipw.SetWindowLevel(window, level)
            ipw.On()

    def setAllOverlayLookupTables(self):
        if len(self._ipws) > 1:
            for ipw in self._ipws[1:]:
                self._setOverlayLookupTable(ipw)

    def _setOverlayLookupTable(self, ipw):
        """Configures overlay lookup table according to mode.

        fusion: the whole overlay gets constast alpha == srcAlpha.
        greenOpacityRange: the overlay gets pure green, opacity 0.0 -> 1.0
        hueOpacityRange: the overlay gets hue and opacity 0.0 -> 1.0
        """

        redHue = 0.0
        greenHue = 0.335
        blueHue = 0.670

        inputStream = ipw.GetInput()
        minv, maxv = inputStream.GetScalarRange()

        lut = ipw.GetLookupTable()
        lut.SetTableRange((minv,maxv))

        mode = self.overlayMode
        srcAlpha = self.fusionAlpha

        if mode == 'greenFusion':
            lut.SetHueRange((greenHue, greenHue))
            lut.SetAlphaRange((srcAlpha, srcAlpha))
            lut.SetValueRange((0.0, 1.0))
            lut.SetSaturationRange((1.0, 1.0))

        elif mode == 'redFusion':
            lut.SetHueRange((redHue, redHue))
            lut.SetAlphaRange((srcAlpha, srcAlpha))
            lut.SetValueRange((0.0, 1.0))
            lut.SetSaturationRange((1.0, 1.0))

        elif mode == 'blueFusion':
            lut.SetHueRange((blueHue, blueHue))
            lut.SetAlphaRange((srcAlpha, srcAlpha))
            lut.SetValueRange((0.0, 1.0))
            lut.SetSaturationRange((1.0, 1.0))

        elif mode == 'hueFusion':
            lut.SetHueRange((0.0, 0.85))
            lut.SetAlphaRange((srcAlpha, srcAlpha))
            lut.SetValueRange((1.0, 1.0))
            lut.SetSaturationRange((1.0, 1.0))

        elif mode == 'hueValueFusion':
            lut.SetHueRange((0.0, 1.0))
            lut.SetAlphaRange((srcAlpha, srcAlpha))
            lut.SetValueRange((0.0, 1.0))
            lut.SetSaturationRange((1.0, 1.0))
            
        elif mode == 'greenOpacityRange':
            lut.SetHueRange((greenHue, greenHue))
            lut.SetAlphaRange((0.0, 1.0))
            lut.SetValueRange((1.0, 1.0))
            lut.SetSaturationRange((1.0, 1.0))

        elif mode == 'redOpacityRange':
            lut.SetHueRange((redHue, redHue))
            lut.SetAlphaRange((0.0, 1.0))
            lut.SetValueRange((1.0, 1.0))
            lut.SetSaturationRange((1.0, 1.0))

        elif mode == 'blueOpacityRange':
            lut.SetHueRange((blueHue, blueHue))
            lut.SetAlphaRange((0.0, 1.0))
            lut.SetValueRange((1.0, 1.0))
            lut.SetSaturationRange((1.0, 1.0))

        elif mode == 'hueOpacityRange':
            lut.SetHueRange((0.0, 1.0))
            lut.SetAlphaRange((0.0, 1.0))
            lut.SetValueRange((1.0, 1.0))
            lut.SetSaturationRange((1.0, 1.0))

        elif mode == 'primaryLUTFusion':
            # we can only be called if there are more IPWs
            # get lut of primary ipw
            primaryIPW = self._ipws[0]
            primaryLUT = primaryIPW.GetLookupTable()
            lut.SetHueRange(primaryLUT.GetHueRange())
            lut.SetAlphaRange((srcAlpha, srcAlpha))
            lut.SetValueRange(primaryLUT.GetValueRange())
            lut.SetSaturationRange(primaryLUT.GetSaturationRange())
            lut.SetTableRange(primaryLUT.GetTableRange())

        lut.Build()
        

    def _syncAllToPrimary(self):
        """This will synchronise everything that can be synchronised to
        the primary.
        """
        self._syncOverlays()
        self._syncOrthoView()
        self._syncContours()
        if self._orthoViewFrame:
            self._orthoViewFrame.RWI.Render()

        self._syncOutputPolyData()
        

    def _syncContours(self):
        """Synchronise all contours to current primary plane.
        """
        for contourObject in self._contourObjectsDict.keys():
            self.syncContourToObject(contourObject)

    def _syncOutputPolyData(self):
        if len(self._ipws) > 0:
            ps = self._ipws[0].GetPolyDataAlgorithm()
            self._primaryCopyPlaneSource.SetOrigin(ps.GetOrigin())
            self._primaryCopyPlaneSource.SetPoint1(ps.GetPoint1())
            self._primaryCopyPlaneSource.SetPoint2(ps.GetPoint2())

    def _syncOverlays(self):
        """Synchronise overlays to current main IPW.
        """
        
        # check that we do have overlays for this direction
        if len(self._ipws) > 1:
            # we know this is a vtkPlaneSource
            try:
                pds1 = self._ipws[0].GetPolyDataAlgorithm()
            except AttributeError:
                pds1 = self._ipws[0].GetPolyDataSource()
            
            for ipw in self._ipws[1:]:
                try:
                    pds2 = ipw.GetPolyDataAlgorithm()
                except AttributeError:
                    pds2 = ipw.GetPolyDataSource()
                
                pds2.SetOrigin(pds1.GetOrigin())
                pds2.SetPoint1(pds1.GetPoint1())
                pds2.SetPoint2(pds1.GetPoint2())
            
                ipw.UpdatePlacement()

    def _syncOrthoView(self):
        """Synchronise all layers of orthoView with what's happening
        with our primary and overlays.
        """

        if self._orthoPipeline and self._ipws:
            # vectorN is pointN - origin
            v1 = [0,0,0]
            self._ipws[0].GetVector1(v1)
            n1 = vtk.vtkMath.Normalize(v1)
            v2 = [0,0,0]
            self._ipws[0].GetVector2(v2)
            n2 = vtk.vtkMath.Normalize(v2)

            roBounds = self._ipws[0].GetResliceOutput().GetBounds()

            for layer in range(len(self._orthoPipeline)):
                planeSource = self._orthoPipeline[layer]['planeSource']
                planeSource.SetOrigin(0,0,0)
                planeSource.SetPoint1(n1, 0, 0)
                planeSource.SetPoint2(0, n2, 0)

                tm2p = self._orthoPipeline[layer]['textureMapToPlane']
                tm2p.SetOrigin(0,0,0)
                tm2p.SetPoint1(roBounds[1] - roBounds[0], 0, 0)
                tm2p.SetPoint2(0, roBounds[3] - roBounds[2], 0)

    def _ipwStartInteractionCallback(self):
        self.sliceDirections.setCurrentSliceDirection(self)
        self._ipwInteractionCallback()

    def _ipwInteractionCallback(self):
        cd = 4 * [0.0]
        if self._ipws[0].GetCursorData(cd):
            self.sliceDirections.setCurrentCursor(cd)

        # find the orthoView (if any) which tracks this IPW
        #directionL = [v['direction'] for v in self._orthoViews
        #              if v['direction'] == direction]
        
        #if directionL:
        #    self._syncOrthoViewWithIPW(directionL[0])
        #    [self._viewFrame.ortho1RWI, self._viewFrame.ortho2RWI]\
        #                                [directionL[0]].Render()

    def _ipwEndInteractionCallback(self):
        # we probably don't have to do all of this, as an interaction
        # can also be merely the user mousing around with the cursor!
        self._syncOverlays()
        self._syncOrthoView()
        self._syncContours()
        if self._orthoViewFrame:
            self._orthoViewFrame.RWI.Render()

        self._syncOutputPolyData()


