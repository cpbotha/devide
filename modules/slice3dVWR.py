# slice3d_vwr.py copyright (c) 2002 Charl P. Botha <cpbotha@ieee.org>
# $Id: slice3dVWR.py,v 1.32 2003/06/16 15:22:16 cpbotha Exp $
# next-generation of the slicing and dicing dscas3 module

import cPickle
from external.SwitchColourDialog import ColourDialog
from genUtils import logError
from genMixins import subjectMixin
from moduleBase import moduleBase
from moduleMixins import vtkPipelineConfigModuleMixin, colourDialogMixin
import moduleUtils
import vtk
from wxPython.wx import *
from wxPython.grid import *
from wxPython.lib import colourdb
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor
import operator

# -------------------------------------------------------------------------
class sliceDirection:
    """Class encapsulating all logic behind a single direction.

    This class contains the IPWs and related paraphernalia for all layers
    (primary + overlays) representing a single view direction.  It optionally
    has its own window with an orthogonal view.
    """

    def __init__(self, name, slice3dViewer, defaultPlaneOrientation=2):
        self._name = name
        self._slice3dViewer = slice3dViewer
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

                if inputData.GetWholeExtent() == \
                   mainInput.GetWholeExtent() and \
                   inputData.GetSpacing() == mainInput.GetSpacing():

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
                self._ipws[-1].SetInput(inputData)
                self._ipws[-1].SetPicker(self._slice3dViewer.getIPWPicker())
                self._ipws[-1].GetImageMapToColors().SetOutputFormatToRGB()

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

    def close(self):
        """Shut down everything."""

        # take out the orthoView
        self.destroyOrthoView()

        # first take care of all our ipws
        inputDatas = [i.GetInput() for i in self._ipws]
        for inputData in inputDatas:
            self.removeData(inputData)

        # kill the whole list
        del self._ipws

        # make sure we don't point to the sliceviewer
        del self._slice3dViewer
        

    def createOrthoView(self):
        """Create an accompanying orthographic view of the sliceDirection
        encapsulated by this object.
        """

        # there can be only one orthoPipeline
        if not self._orthoPipeline:

            import modules.resources.python.slice3dVWRFrames            
            # import our wxGlade-generated frame
            ovf = modules.resources.python.slice3dVWRFrames.orthoViewFrame
            self._orthoViewFrame = ovf(self._slice3dViewer._viewFrame, id=-1,
                                  title='dummy')

            self._orthoViewFrame.SetIcon(moduleUtils.getModuleIcon())

            self._renderer = vtk.vtkRenderer()
            self._renderer.SetBackground(0.5, 0.5, 0.5)
            self._orthoViewFrame.RWI.GetRenderWindow().AddRenderer(
                self._renderer)
            istyle = vtk.vtkInteractorStyleImage()
            self._orthoViewFrame.RWI.SetInteractorStyle(istyle)

            EVT_CLOSE(self._orthoViewFrame,
                      lambda e, s=self: s.destroyOrthoView)

            EVT_BUTTON(self._orthoViewFrame,
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
        for ipw in self._ipws:
            ipw.On()

    def enableInteraction(self):
        if self._ipws:
            self._ipws[0].SetInteraction(1)

    def disable(self):
        """Switch this sliceDirection off."""
        for ipw in self._ipws:
            ipw.Off()

    def disableInteraction(self):
        if self._ipws:
            self._ipws[0].SetInteraction(0)

    def getEnabled(self):
        if self._ipws:
            return self._ipws[0].GetEnabled()
        else:
            # if we have no ipws yet, we are enabled (because the first ipw
            # will be)
            return 1

    def getInteractionEnabled(self):
        if self._ipws:
            return self._ipws[0].GetInteraction()
        else:
            # if we have no ipws yet, we are interaction enabled
            return 1

    def getOrthoViewEnabled(self):
        return self._orthoViewFrame is not None

    def getName(self):
        return self._name

    def getNumberOfLayers(self):
        return len(self._ipws)

    def pushSlice(self, val):
        if self._ipws:
            self._ipws[0].GetPolyDataSource().Push(val)
            self._ipws[0].UpdatePlacement()
            self._ipwEndInteractionCallback()

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
            # disconnect the input
            ipw.SetInput(None)
            # finally delete our reference
            idx = self._ipws.index(ipw)
            del self._ipws[idx]

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
                inputStream = ipw.GetInput()
                minv, maxv = inputStream.GetScalarRange()
                lut.SetTableRange((minv,maxv))
                lut.SetAlphaRange((0.0, 1.0))
                lut.SetValueRange((1.0, 1.0))
                lut.SetSaturationRange((1.0, 1.0))
                lut.Build()

                ipw.SetInteractor(self._slice3dViewer._viewFrame.threedRWI)
                # default axial orientation
                ipw.SetPlaneOrientation(self._defaultPlaneOrientation)
                ipw.SetSliceIndex(0)
                
                ipw.SetLookupTable(lut)
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
            
            # calculate default window/level once
            (dmin,dmax) = inputData.GetScalarRange()
            iwindow = (dmax - dmin) / 2
            ilevel = dmin + iwindow

            inputData_source = inputData.GetSource()
            if hasattr(inputData_source, 'GetWindowCenter') and \
                   callable(inputData_source.GetWindowCenter):
                level = inputData_source.GetWindowCenter()
                print "Retrieved level of %f" % level
            else:
                level = ilevel

            if hasattr(inputData_source, 'GetWindowWidth') and \
                   callable(inputData_source.GetWindowWidth):
                window = inputData_source.GetWindowWidth()
                print "Retrieved window of %f" % window
            else:
                window = iwindow

            lut = vtk.vtkWindowLevelLookupTable()
            lut.SetWindow(window)
            lut.SetLevel(level)
            lut.Build()

            # colours of imageplanes; we will use these as keys
            ipw_cols = [(1,0,0), (0,1,0), (0,0,1)]

            ipw = self._ipws[0]
            ipw.DisplayTextOn()
            ipw.SetInteractor(self._slice3dViewer._viewFrame.threedRWI)
            ipw.SetPlaneOrientation(self._defaultPlaneOrientation)
            ipw.SetSliceIndex(0)
            ipw.GetPlaneProperty().SetColor(
                ipw_cols[ipw.GetPlaneOrientation()])
            # this is not working yet, because the IPWs handling of
            # luts is somewhat broken at the moment
            ipw.SetLookupTable(lut)
            ipw.On()

    def _syncOverlays(self):
        """Synchronise overlays to current main IPW.
        """
        
        # check that we do have overlays for this direction
        if len(self._ipws) > 1:
            # we know this is a vtkPlaneSource
            pds1 = self._ipws[0].GetPolyDataSource()

            for ipw in self._ipws[1:]:
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
        self._slice3dViewer.setCurrentSliceDirection(self)
        self._ipwInteractionCallback()

    def _ipwInteractionCallback(self):
        cd = 4 * [0.0]
        if self._ipws[0].GetCursorData(cd):
            self._slice3dViewer.setCurrentCursor(cd)

        # find the orthoView (if any) which tracks this IPW
        #directionL = [v['direction'] for v in self._orthoViews
        #              if v['direction'] == direction]
        
        #if directionL:
        #    self._syncOrthoViewWithIPW(directionL[0])
        #    [self._viewFrame.ortho1RWI, self._viewFrame.ortho2RWI]\
        #                                [directionL[0]].Render()

    def _ipwEndInteractionCallback(self):
        self._syncOverlays()
        self._syncOrthoView()
        if self._orthoViewFrame:
            self._orthoViewFrame.RWI.Render()
                
        
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

class tdObjects:

    _objectColours = ['LIMEGREEN', 'SKYBLUE', 'PERU', 'CYAN', 
                      'GOLD',  'MAGENTA', 'GREY80',
                      'PURPLE']

    _gridNameCol = 0
    _gridColourCol = 1
    _gridVisibleCol = 2

    def __init__(self, slice3dVWRThingy, grid):
        self._tdObjectsDict = {}
        self._objectId = 0
        
        self._slice3dVWR = slice3dVWRThingy
        self._grid = grid
        self._initialiseGrid()
        self._bindEvents()

        # this will fix up wxTheColourDatabase
        colourdb.updateColourDB()

    def close(self):
        self._tdObjectsDict.clear()
        self._slice3dVWR = None
        self._grid.ClearGrid()
        self._grid = None

    def _bindEvents(self):
        svViewFrame = self._slice3dVWR.getViewFrame()
        EVT_BUTTON(svViewFrame, svViewFrame.objectSetColourButtonId,
                   self._handlerObjectSetColour)
        
        EVT_BUTTON(svViewFrame, svViewFrame.objectShowHideButtonId,
                   self._handlerObjectShowHideHandler)

    def _handlerObjectSetColour(self, event):
        # get the first selected row in the grid
        selectedRows = self._grid.GetSelectedRows()
        if selectedRows:
            objectNames = []
            for sRow in selectedRows:
                objectNames.append(
                    self._grid.GetCellValue(sRow, self._gridNameCol)
                    )

            objs = self.findObjectsByNames(objectNames)

            if objs:
                self._slice3dVWR.setColourDialogColour(
                    self._tdObjectsDict[objs[0]]['colour'])
                
                dColour = self._slice3dVWR.getColourDialogColour()
                if dColour:
                    for obj in objs:
                        self._setObjectColour(obj, dColour)

    def _handlerObjectShowHideHandler(self, event):
        pass
        
    def _initialiseGrid(self):
        """Setup the object listCtrl from scratch, mmmkay?
        """

        # delete all items and columns
        self._grid.DeleteRows(0, self._grid.GetNumberRows())

        self._grid.SetColSize(self._gridNameCol, 100)
        self._grid.SetColSize(self._gridColourCol, 150)
        self._grid.SetColSize(self._gridVisibleCol, 50)

    def addObject(self, tdObject):
        """Takes care of all the administration of adding a new 3-d object
        to the list and updating it in the list control.
        """

        if not self._tdObjectsDict.has_key(tdObject):

            # we get to pick a colour and a name
            colourName = self._objectColours[
                self._objectId % len(self._objectColours)]
            # objectName HAS TO BE unique!
            objectName = "%s%d" % ('obj', self._objectId)
            self._objectId += 1

            # create a colour as well
            colour = wxTheColourDatabase.FindColour(colourName).asTuple()
            # normalise
            nColour = tuple([c / 255.0 for c in colour])

            # now actually create the necessary thingies and add the object
            # to the scene
            if hasattr(tdObject, 'GetClassName') and \
               callable(tdObject.GetClassName):

                if tdObject.GetClassName() == 'vtkVolume':
                    self._slice3dVWR._threedRenderer.AddVolume(tdObject)
                    self._tdObjectsDict[tdObject] = {'tdObject' : tdObject,
                                                     'type' : 'vtkVolume',
                                                     'observerId' : None}

                elif tdObject.GetClassName() == 'vtkPolyData':
                    mapper = vtk.vtkPolyDataMapper()
                    mapper.SetInput(tdObject)
                    actor = vtk.vtkActor()
                    actor.SetMapper(mapper)
                    self._slice3dVWR._threedRenderer.AddActor(actor)
                    self._tdObjectsDict[tdObject] = {'tdObject' : tdObject,
                                                     'type' : 'vtkPolyData',
                                                     'vtkActor' : actor,
                                                     'observerId' : None}

                    # to get the name of the scalars we need to do this.
                    tdObject.Update()
                
                    # now some special case handling
                    if tdObject.GetPointData().GetScalars():
                        sname = tdObject.GetPointData().GetScalars().GetName()
                    else:
                        sname = None
                
                    if sname and sname.lower().find("curvature") >= 0:
                        # if the active scalars have "curvature" somewhere in
                        # their name, activate flat shading and scalar vis
                        property = actor.GetProperty()
                        property.SetInterpolationToFlat()
                        mapper.ScalarVisibilityOn()
                    
                    else:
                        # the user can switch this back on if she really
                        # wants it
                        # we switch it off as we mostly work with isosurfaces
                        mapper.ScalarVisibilityOff()
                
                    # connect an event handler to the data
                    source = tdObject.GetSource()
                    if source:
                        oid = source.AddObserver(
                            'EndEvent',
                            self._tdObjectModifiedCallback)
                        self._tdObjectsDict[tdObject]['observerId'] = oid

                else:
                    raise Exception, 'Non-handled tdObject type'

            else:
                # the object has no GetClassName that's callable
                raise Exception, 'tdObject has no GetClassName()'

            nrGridRows = self._grid.GetNumberRows()
            self._grid.AppendRows()
            self._grid.SetCellValue(nrGridRows, 0, objectName)
            self._grid.SetCellValue(nrGridRows, 1, colourName)
            self._grid.SetCellValue(nrGridRows, 2, 'Yes')
            
            self._tdObjectsDict[tdObject]['objectName'] = objectName
            # and store the colour
            self._setObjectColour(tdObject, nColour)

            self._slice3dVWR._threedRenderer.ResetCamera()
            self._slice3dVWR.render3D()
            
        # ends 
        else:
            raise Exception, 'Attempt to add same object twice.'

    def findGridRowByName(self, objectName):
        nrGridRows = self._grid.GetNumberRows()
        rowFound = False
        row = 0

        while not rowFound and row < nrGridRows:
            value = self._grid.GetCellValue(row, self._gridNameCol)
            rowFound = (value == objectName)
            row += 1

        if rowFound:
            # prepare and return the row
            row -= 1
            return row
        
        else:
            return -1

    def findObjectsByNames(self, objectNames):
        """Given an objectName, return an object binding.
        """
        
        dictItems = self._tdObjectsDict.items()
        dictLen = len(dictItems)

        objectFound = False
        itemsIdx = 0

        while not objectFound and itemsIdx < dictLen:
            objectFound = objectName == dictItems[itemsIdx][1]['objectName']
            itemsIdx += 1

        if objectFound:
            itemsIdx -= 1
            return dictItems[itemsIdx][0]
        else:
            return None

    def findObjectsByNames(self, objectNames):
        """Given a sequence of object names, return a sequence with bindings
        to all the found objects.  There could be less objects than names.
        """

        dictItems = self._tdObjectsDict.items()
        dictLen = len(dictItems)

        itemsIdx = 0
        foundObjects = []

        while itemsIdx < dictLen:
            if dictItems[itemsIdx][1]['objectName'] in objectNames:
                foundObjects.append(dictItems[itemsIdx][0])

            itemsIdx += 1

        return foundObjects
            

    def removeObject(self, tdObject):
        if not self._tdObjectsDict.has_key(tdObject):
            raise Exception, 'Attempt to remove non-existent tdObject'

        oType = self._tdObjectsDict[tdObject]['type']
        if oType == 'vtkVolume':
            self._slice3dVWR._threedRenderer.RemoveVolume(tdObject)
            self._slice3dVWR.render3D()

        elif oType == 'vtkPolyData':
            actor = self._tdObjectsDict[tdObject]['vtkActor']
            self._slice3dVWR._threedRenderer.RemoveActor(actor)
            if self._tdObjectsDict[tdObject]['observerId']:
                source = actor.GetMapper().GetInput().GetSource()
                if source:
                    source.RemoveObserver(
                        self._tdObjectsDict[tdObject]['observerId'])
                    
                # whether we had a source or not, zero this
                self._tdObjectsDict[tdObject]['observerId'] = None

            self._slice3dVWR.render3D()
            
        else:
            raise Exception,\
                  'Unhandled object type in tdObjects.removeObject()'

        # whatever the case may be, we need to remove it from the wxGrid
        # first search for the correct objectName
        nrGridRows = self._grid.GetNumberRows()
        rowFound = False
        row = 0
        objectName = self._tdObjectsDict[tdObject]['objectName']

        while not rowFound and row < nrGridRows:
            value = self._grid.GetCellValue(row, self._gridNameCol)
            rowFound = value == objectName
            row += 1

        if rowFound:
            # and then delete just that row
            row -= 1
            self._grid.DeleteRows(row)
            
        # and from the dict
        del self._tdObjectsDict[tdObject]

    def _setObjectColour(self, tdObject, dColour):
        if self._tdObjectsDict.has_key(tdObject):
            if self._tdObjectsDict[tdObject]['type'] == 'vtkPolyData':
                objectDict = self._tdObjectsDict[tdObject]
                
                # in our metadata
                objectDict['colour'] = dColour
                
                # change its colour in the scene                
                actor = objectDict['vtkActor']
                actor.GetProperty().SetDiffuseColor(dColour)

                # and change its colour in the grid
                row = self.findGridRowByName(objectDict['objectName'])
                if row >= 0:
                    r,g,b = [c * 255.0 for c in dColour]
                    colour = wxColour(r,g,b)
                    self._grid.SetCellBackgroundColour(
                        row, self._gridColourCol, colour)
                    
                    # also search for the name
                    cName = wxTheColourDatabase.FindName(colour)
                    if not cName:
                        cName = 'USER DEFINED'

                    self._grid.SetCellValue(row, self._gridColourCol, cName)
                    

    def _tdObjectModifiedCallback(self, o, e):
        self._slice3dVWR.render3D()

# -------------------------------------------------------------------------

class slice3dVWR(moduleBase, vtkPipelineConfigModuleMixin, colourDialogMixin):
    
    """Slicing, dicing slice viewing class.

    This class is used as a dscas3 module.  Given vtkImageData-like input data,
    it will show 3 slices and 3 planes in a 3d scene.  PolyData objects can
    also be added.  One can interact with the 3d slices to change the slice
    orientation and position.
    """

    def __init__(self, moduleManager):
        # call base constructor
        moduleBase.__init__(self, moduleManager)
        colourDialogMixin.__init__(
            self, moduleManager.get_module_view_parent_window())
        self._numDataInputs = 5
        # use list comprehension to create list keeping track of inputs
        self._inputs = [{'Connected' : None, 'inputData' : None,
                         'observerID' : -1,
                         'vtkActor' : None, 'ipw' : None}
                       for i in range(self._numDataInputs)]
        # then the window containing the renderwindows
        self._viewFrame = None
        # the imageplanewidgets: a 3-element (axial, coronal, sagittal) list
        # of lists of IPWs (each direction list contains the primary IPW
        # as well as all overlays)
        self._sliceDirections = []
        self._currentSliceDirection = None
        # this same picker is used on all new IPWS of all sliceDirections
        self._ipwPicker = vtk.vtkCellPicker()
        # the renderers corresponding to the render windows
        self._threedRenderer = None

        self._currentCursor = None
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

        # set the whole UI up!
        self._create_window()

        # we now have a wxListCtrl, let's abuse it
        self._tdObjects = tdObjects(self,
                                    self._viewFrame.objectsListGrid)

        # create a default slice
        self._createSlice('Axial')

    #################################################################
    # module API methods
    #################################################################
        

    def close(self):
        print "starting close"

        # take care of scalarbar
        self._showScalarBarForProp(None)
        
        # this is standard behaviour in the close method:
        # call set_input(idx, None) for all inputs
        for idx in range(self._numDataInputs):
            self.setInput(idx, None)

        # take care of the sliceDirections
        for sliceDirection in self._sliceDirections:
            sliceDirection.close()

        del self._sliceDirections

        # don't forget to call the mixin close() methods
        vtkPipelineConfigModuleMixin.close(self)
        colourDialogMixin.close(self)
        
        # unbind everything that we bound in our __init__
        del self._outline_source
        del self._outline_actor
        del self._cube_axes_actor2d
        del self._voi_widget
        del self._extractVOI
        
        # take care of all our bindings to renderers
        del self._threedRenderer

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

        #self._viewFrame.threedRWI.GetRenderWindow().SetSize(10,10)
        self._viewFrame.threedRWI.GetRenderWindow().WindowRemap()        
        
        # all the RenderWindow()s are now reparented, so we can destroy
        # the containing frame
        self._viewFrame.Destroy()
        # unbind the _view_frame binding
        del self._viewFrame

    def getConfig(self):
        # implant some stuff into the _config object and return it

        # all points from the self._selectedPoints list
        savedPoints = []
        for sp in self._selectedPoints:
            savedPoints.append({'discrete' : sp['discrete'],
                                'world' : sp['world'],
                                'value' : sp['value'],
                                'name' : sp['name'],
                                'lockToSurface' : sp['lockToSurface']})

        self._config.savedPoints = savedPoints            

        # also save the visible bounds (this will be used during unpickling
        # to calculate pointwidget and text sizes and the like)
        self._config.boundsForPoints = self._threedRenderer.\
                                       ComputeVisiblePropBounds()        

        
        return self._config

    def setConfig(self, aConfig):
        self._config = aConfig

        savedPoints = self._config.savedPoints

        for sp in savedPoints:
            self._storePoint(sp['discrete'], sp['world'], sp['value'],
                             sp['name'], sp['lockToSurface'],
                             self._config.boundsForPoints)

    def getInputDescriptions(self):
        # concatenate it num_inputs times (but these are shallow copies!)
        return self._numDataInputs * \
               ('vtkStructuredPoints|vtkImageData|vtkPolyData',)

    def setInput(self, idx, input_stream):
        if input_stream == None:
            if self._inputs[idx]['Connected'] == 'tdObject':
                self._tdObjects.removeObject(self._inputs[idx]['tdObject'])
                self._inputs[idx]['Connected'] = None
                self._inputs[idx]['tdObject'] = None

            elif self._inputs[idx]['Connected'] == 'vtkImageDataPrimary' or \
                 self._inputs[idx]['Connected'] == 'vtkImageDataOverlay':

                for sliceDirection in self._sliceDirections:
                    sliceDirection.removeData(self._inputs[idx]['inputData'])

                # remove our observer
                if self._inputs[idx]['observerID'] >= 0:
                    source = self._inputs[idx]['inputData'].GetSource()
                    if source:
                        source.RemoveObserver(
                            self._inputs[idx]['observerID'])
                    # whether we had a source or not, make sure to zero this
                    self._inputs[idx]['observerID'] = -1

                if self._inputs[idx]['Connected'] == 'vtkImageDataPrimary':
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

                self._inputs[idx]['Connected'] = None
                self._inputs[idx]['inputData'] = None

        # END of if input_stream is None clause -----------------------------

        elif hasattr(input_stream, 'GetClassName') and \
             callable(input_stream.GetClassName):

            if input_stream.GetClassName() == 'vtkVolume' or \
               input_stream.GetClassName() == 'vtkPolyData':
                # our _tdObjects instance likes to do this
                self._tdObjects.addObject(input_stream)
                # if this worked, we have to make a note that it was
                # connected as such
                self._inputs[idx]['Connected'] = 'tdObject'
                self._inputs[idx]['tdObject'] = input_stream
                
            elif input_stream.IsA('vtkImageData'):

                try:
                    # add this input to all available sliceDirections
                    for sliceDirection in self._sliceDirections:
                        sliceDirection.addData(input_stream)
                    
                except Exception, msg:
                    # if an exception was thrown, clean up and raise again
                    for sliceDirection in self._sliceDirections:
                        sliceDirection.removeData(input_stream)

                    raise Exception, msg

                # find out whether this is  primary or an overlay, record it
                connecteds = [i['Connected'] for i in self._inputs]
                if 'vtkImageDataPrimary' in connecteds or \
                       'vtkImageDataOverlay' in connecteds:
                    # this must be an overlay
                    self._inputs[idx]['Connected'] = 'vtkImageDataOverlay'
                else:
                    # there are no primaries or overlays, this must be
                    # a primary then
                    self._inputs[idx]['Connected'] = 'vtkImageDataPrimary'

                # also store binding to the data itself
                self._inputs[idx]['inputData'] = input_stream

                # add an observer to this data and store the id
                source = input_stream.GetSource()
                if source:
                    oid = source.AddObserver(
                        'EndEvent',
                        self.inputModifiedCallback)
                    self._inputs[idx]['observerID'] = oid
                
                if self._inputs[idx]['Connected'] == 'vtkImageDataPrimary':
                    # things to setup when primary data is added
                    self._extractVOI.SetInput(input_stream)

                    # add outline actor and cube axes actor to renderer
                    self._threedRenderer.AddActor(self._outline_actor)
                    self._outline_actor.PickableOff()
                    self._threedRenderer.AddActor(self._cube_axes_actor2d)
                    self._cube_axes_actor2d.PickableOff()
                    # FIXME: make this toggle-able
                    self._cube_axes_actor2d.VisibilityOff()

                    # reset everything, including ortho camera
                    self._resetAll()

                # update our 3d renderer
                self._viewFrame.threedRWI.Render()

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
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()

    #################################################################
    # miscellaneous public methods
    #################################################################

    def getIPWPicker(self):
        return self._ipwPicker

    def getViewFrame(self):
        return self._viewFrame

    def render3D(self):
        """This will cause a render to be called on the encapsulated 3d
        RWI.
        """
        self._viewFrame.threedRWI.Render()

    def setCurrentCursor(self, cursor):
        self._currentCursor = cursor
        cstring = str(self._currentCursor[0:3]) + " = " + \
                  str(self._currentCursor[3])
        
        self._viewFrame.sliceCursorText.SetValue(cstring)
        

    #################################################################
    # internal utility methods
    #################################################################

    def _createSlice(self, sliceName):
        #sliceName = self._viewFrame.createSliceText.GetValue()
        if sliceName:
            names = [i.getName() for i in self._sliceDirections]
            if sliceName in names:
                wxLogError("A slice with that name already exists.")

            else:
                self._sliceDirections.append(sliceDirection(sliceName, self))
                # now attach all inputs to it
                for i in self._inputs:
                    if i['Connected'] == 'vtkImageDataPrimary' or \
                           i['Connected'] == 'vtkImageDataOverlay':
                        self._sliceDirections[-1].addData(i['inputData'])

                # add it to the GUI choice
                self._viewFrame.sliceNameChoice.Append(sliceName)
                self.setCurrentSliceDirection(self._sliceDirections[-1])
                #self._viewFrame.sliceNameChoice.SetStringSelection(sliceName)

    def _create_window(self):
        import modules.resources.python.slice3dVWRFrames
        reload(modules.resources.python.slice3dVWRFrames)

        # create main frame, make sure that when it's closed, it merely hides
        parent_window = self._moduleManager.get_module_view_parent_window()
        slice3d_vwr_frame = modules.resources.python.slice3dVWRFrames.\
                            MainFrame
        self._viewFrame = slice3d_vwr_frame(parent_window, id=-1,
                                             title='dummy')

        self._viewFrame.SetIcon(moduleUtils.getModuleIcon())

        # fix for the grid
        self._viewFrame.spointsGrid.SetSelectionMode(wxGrid.wxGridSelectRows)
        # fix for the choice *sigh*
        self._viewFrame.sliceNameChoice.Clear()

        # add the renderer
        self._threedRenderer = vtk.vtkRenderer()
        self._threedRenderer.SetBackground(0.5, 0.5, 0.5)
        self._viewFrame.threedRWI.GetRenderWindow().AddRenderer(self.
                                                               _threedRenderer)

        # make sure it's a trackball actor style thingy
        istyle = vtk.vtkInteractorStyleTrackballCamera()
        self._viewFrame.threedRWI.SetInteractorStyle(istyle)

        # add possible point names
        self._viewFrame.sliceCursorNameCombo.Clear()
        self._viewFrame.sliceCursorNameCombo.Append('Point 1')
        self._viewFrame.sliceCursorNameCombo.Append('GIA Glenoid')
        self._viewFrame.sliceCursorNameCombo.Append('GIA Humerus')
        self._viewFrame.sliceCursorNameCombo.Append('FBZ Superior')
        self._viewFrame.sliceCursorNameCombo.Append('FBZ Inferior')
        
        # event handlers for the global control buttons
        EVT_BUTTON(self._viewFrame, self._viewFrame.pipelineButtonId,
                   lambda e, pw=self._viewFrame, s=self,
                   rw=self._viewFrame.threedRWI.GetRenderWindow():
                   s.vtkPipelineConfigure(pw, rw))

        EVT_BUTTON(self._viewFrame, self._viewFrame.resetButtonId,
                   lambda e, s=self: s._resetAll())

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

        def saveListCallback(event):
            self._syncOutputSelectedPoints()
            cPickle.Pickler(sys.stdout).dump(self._outputSelectedPoints)
            pass

        def loadListCallback(event):
            pass

        EVT_BUTTON(self._viewFrame, self._viewFrame.saveListButtonId,
                   saveListCallback)
        EVT_BUTTON(self._viewFrame, self._viewFrame.loadListButtonId,
                   loadListCallback)
        

        def pointInteractionCheckBoxCallback(event):
            val = self._viewFrame.pointInteractionCheckBox.GetValue()
            if val:
                for selectedPoint in self._selectedPoints:
                    if selectedPoint['pointWidget']:
                        selectedPoint['pointWidget'].On()
                        
            else:
                for selectedPoint in self._selectedPoints:
                    if selectedPoint['pointWidget']:
                        selectedPoint['pointWidget'].Off()

        EVT_CHECKBOX(self._viewFrame,
                     self._viewFrame.pointInteractionCheckBoxId,
                     pointInteractionCheckBoxCallback)

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

        EVT_CHOICE(self._viewFrame, self._viewFrame.sliceNameChoiceId,
                   self._sliceNameChoiceCallback)

        # first a callback for turning an IPW on or off

        def _eb_cb():
            sliceDirection = self._getCurrentSliceDirection()
            if sliceDirection:
                if self._viewFrame.sliceEnabledCheckBox.GetValue():
                    sliceDirection.enable()
                                
                    self._viewFrame.sliceInteractionCheckBox.Enable(1)
                    self._viewFrame.pushSliceLabel.Enable(1)
                    self._viewFrame.pushSliceSpinCtrl.Enable(1)
                        
                else:
                    sliceDirection.disable()

                    self._viewFrame.sliceInteractionCheckBox.Enable(0)
                    self._viewFrame.pushSliceLabel.Enable(0)
                    self._viewFrame.pushSliceSpinCtrl.Enable(0)
                    
    

        EVT_BUTTON(self._viewFrame, self._viewFrame.createSliceButtonId,
                   lambda e, s=self: s._createSlice(
            s._viewFrame.createSliceText.GetValue()))

        EVT_BUTTON(self._viewFrame, self._viewFrame.destroySliceButtonId,
                   lambda e, s=self: s._destroySlice())
                        
        
        EVT_CHECKBOX(self._viewFrame, self._viewFrame.sliceEnabledCheckBoxId,
                     lambda e: _eb_cb())

        EVT_CHOICE(self._viewFrame, self._viewFrame.acsChoiceId,
                   lambda e, s=self: s._acsChoiceCallback())

        def _ib_cb():
            sliceDirection = self._getCurrentSliceDirection()
            if sliceDirection:
                if self._viewFrame.sliceInteractionCheckBox.GetValue():
                    sliceDirection.enableInteraction()
                else:
                    sliceDirection.disableInteraction()
                
        EVT_CHECKBOX(self._viewFrame,
                     self._viewFrame.sliceInteractionCheckBoxId,
                     lambda e: _ib_cb())

        def _ov_cb():
            sliceDirection = self._getCurrentSliceDirection()
            if sliceDirection:
                if self._viewFrame.orthoViewCheckBox.GetValue():
                    sliceDirection.createOrthoView()
                else:
                    sliceDirection.destroyOrthoView()

        EVT_CHECKBOX(self._viewFrame,
                     self._viewFrame.orthoViewCheckBoxId,
                     lambda e: _ov_cb())

        def _ps_cb():
            sliceDirection  = self._getCurrentSliceDirection()
            if sliceDirection:
                val = self._viewFrame.pushSliceSpinCtrl.GetValue()
                if val:
                    sliceDirection.pushSlice(val)
                    self._viewFrame.pushSliceSpinCtrl.SetValue(0)
                    self._viewFrame.threedRWI.Render()

        EVT_SPINCTRL(self._viewFrame, self._viewFrame.pushSliceSpinCtrlId,
                     lambda e: _ps_cb())

        # the store button
        EVT_BUTTON(self._viewFrame, self._viewFrame.sliceStoreButtonId,
                   lambda e: self._storeCursorCallback())

        # clicks directly in the window for picking
        self._viewFrame.threedRWI.AddObserver('LeftButtonPressEvent',
                                               self._rwiLeftButtonCallback)
        
        # attach close handler
        EVT_CLOSE(self._viewFrame,
                  lambda e, s=self: s._viewFrame.Show(false))

        # display the window
        self._viewFrame.Show(True)


    def _destroySlice(self):
        """Destroy the currently selected slice."""

        sliceDirection = self._getCurrentSliceDirection()
        if sliceDirection:
            name = sliceDirection.getName()
            # this will disconnect all inputs
            sliceDirection.close()
            # delete it from our internal list
            idx = self._sliceDirections.index(sliceDirection)
            del self._sliceDirections[idx]
            # remove it from the choice thingy
            idx = self._viewFrame.sliceNameChoice.FindString(name)
            self._viewFrame.sliceNameChoice.Delete(idx)
            self._viewFrame.sliceNameChoice.SetSelection(1)

    def _findSliceDirectionByName(self, name):
        sliceDirectionL = [i for i in self._sliceDirections if
                          i.getName() == name]
                           
        if sliceDirectionL:
           return sliceDirectionL[0]
        else:
           return None
        

    def _getCurrentSliceDirection(self):
        return self._currentSliceDirection

    def _getPrimaryInput(self):
        """Get primary input data, i.e. bottom layer.

        If there is no primary input data, this will return None.
        """
        
        inputs = [i for i in self._inputs if i['Connected'] ==
                  'vtkImageDataPrimary']

        if inputs:
            inputData = inputs[0]['inputData']
        else:
            inputData = None

        return inputData


    def setCurrentSliceDirection(self, sliceDirection):
        if sliceDirection != self._currentSliceDirection:
            self._currentSliceDirection = sliceDirection
            if sliceDirection is not None:
                name = sliceDirection.getName()
                print name
                self._viewFrame.sliceNameChoice.SetStringSelection(name)
                # update all GUI elements
                self._viewFrame.sliceEnabledCheckBox.SetValue(
                    sliceDirection.getEnabled())
                self._viewFrame.sliceInteractionCheckBox.SetValue(
                    sliceDirection.getInteractionEnabled())
                self._viewFrame.orthoViewCheckBox.SetValue(
                    sliceDirection.getOrthoViewEnabled())
        

    def _remove_cursors(self, idxs):

        # we have to delete one by one from back to front
        idxs.sort()
        idxs.reverse()
        
        for idx in idxs:
            # remove the sphere actor from the renderer
            self._threedRenderer.RemoveActor(self._selectedPoints[idx]['sphereActor'])
            # remove the text_actor (if any)
            if self._selectedPoints[idx]['textActor']:
                self._threedRenderer.RemoveActor(self._selectedPoints[idx]['textActor'])
            
            # then deactivate and disconnect the point widget
            pw = self._selectedPoints[idx]['pointWidget']
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
        

    def _resetAll(self):
        """Arrange everything for a single overlay in a single ortho view.

        This method is to be called AFTER the pertinent VTK pipeline has been
        setup.  This is here, because one often connects modules together
        before source modules have been configured, i.e. the success of this
        method is dependent on whether the source modules have been configged.
        HOWEVER: it won't die if it hasn't, just complain.

        It will configure all 3d widgets and textures and thingies, but it
        won't CREATE anything.
        """

        # we only do something here if we have data
        inputDataL = [i['inputData'] for i in self._inputs
                      if i['Connected'] == 'vtkImageDataPrimary']
        if inputDataL:
            inputData = inputDataL[0]
        else:
            return

        # we might have ipws, but no inputData, in which we can't do anything
        # either, so we bail
        if inputData is None:
            return

        # make sure this is all nicely up to date
        inputData.Update()

        # set up helper actors
        self._outline_source.SetBounds(inputData.GetBounds())
        self._cube_axes_actor2d.SetBounds(inputData.GetBounds())
        self._cube_axes_actor2d.SetCamera(
            self._threedRenderer.GetActiveCamera())

        # reset the VOI widget
        self._voi_widget.SetInteractor(self._viewFrame.threedRWI)
        self._voi_widget.SetInput(inputData)
        self._voi_widget.PlaceWidget()
        self._voi_widget.SetPriority(0.6)
        #self._voi_widget.On()

        self._threedRenderer.ResetCamera()

        # make sure the overlays follow  suit
        for sliceDirection in self._sliceDirections:
            sliceDirection._resetPrimary()
            sliceDirection._resetOverlays()

        # whee, thaaaar she goes.
        self._viewFrame.threedRWI.Render()

    def _showScalarBarForProp(self, prop):
        """Show scalar bar for the data represented by the passed prop.
        If prop is None, the scalar bar will be removed and destroyed if
        present.
        """

        destroyScalarBar = False

        if prop:
            # activate the scalarbar, connect to mapper of prop
            if prop.GetMapper() and prop.GetMapper().GetLookupTable():
                if not hasattr(self, '_pdScalarBarActor'):
                    self._pdScalarBarActor = vtk.vtkScalarBarActor()
                    self._threedRenderer.AddProp(self._pdScalarBarActor)

                sname = "Unknown"
                s = prop.GetMapper().GetInput().GetPointData().GetScalars()
                if s and s.GetName():
                    sname = s.GetName()

                self._pdScalarBarActor.SetTitle(sname)
                    
                self._pdScalarBarActor.SetLookupTable(
                    prop.GetMapper().GetLookupTable())

                self._viewFrame.threedRWI.Render()
                    
            else:
                # the prop doesn't have a mapper or the mapper doesn't
                # have a LUT, either way, we switch off the thingy...
                destroyScalarBar = True

        else:
            # the user has clicked "somewhere else", so remove!
            destroyScalarBar = True
                

        if destroyScalarBar and hasattr(self, '_pdScalarBarActor'):
            self._threedRenderer.RemoveProp(self._pdScalarBarActor)
            del self._pdScalarBarActor
        

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

        inputData = self._getPrimaryInput()
            
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

        pointName = self._viewFrame.sliceCursorNameCombo.GetValue()            
        self._storePoint(discrete, xyz, val, pointName, True) # lock to surface

    def _storeCursor(self, cursor):
        """Store the point represented by the cursor parameter.

        cursor is a 4-tuple with the discrete (data-relative) xyz coords and
        the value at that point.
        """

        inputs = [i for i in self._inputs if i['Connected'] ==
                  'vtkImageDataPrimary']

        if not inputs or not self._currentCursor:
            return

        # we first have to check that we don't have this pos already
        discretes = [i['discrete'] for i in self._selectedPoints]
        if tuple(cursor[0:3]) in discretes:
            return
        
        input_data = inputs[0]['inputData']
        ispacing = input_data.GetSpacing()
        iorigin = input_data.GetOrigin()
        # calculate real coords
        world = map(operator.add, iorigin,
                    map(operator.mul, ispacing, cursor[0:3]))

        pointName = self._viewFrame.sliceCursorNameCombo.GetValue()
        self._storePoint(tuple(cursor[0:3]), tuple(world), cursor[3],
                         pointName)

    def _storePoint(self, discrete, world, value, pointName,
                    lockToSurface=False, boundsForPoints=None):

        if not boundsForPoints:
            bounds = self._threedRenderer.ComputeVisiblePropBounds()
        else:
            bounds = boundsForPoints
        
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

        ss.SetRadius((bounds[1] - bounds[0]) / 100.0)
        sm = vtk.vtkPolyDataMapper()
        sm.SetInput(ss.GetOutput())
        sa = vtk.vtkActor()
        sa.SetMapper(sm)
        sa.SetPosition(world)
        sa.GetProperty().SetColor(1.0,0.0,0.0)
        self._threedRenderer.AddActor(sa)
        sa.SetPickable(0)

        if len(pointName) > 0:
            name_text = vtk.vtkVectorText()
            name_text.SetText(pointName)
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
            ta.SetPickable(0)
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


        # after we've added observers, we get to switch the widget on or
        # off; but it HAS to be on when the observers are added
        if self._viewFrame.pointInteractionCheckBox.GetValue():
            pw.On()
        else:
            pw.Off()

        # store the cursor (discrete coords) the coords and the actor
        self._selectedPoints.append({'discrete' : tuple(discrete),
                                     'world' : tuple(world),
                                     'value' : value,
                                     'name' : pointName,
                                     'pointWidget' : pw,
                                     'lockToSurface' : lockToSurface,
                                     'sphereActor' : sa,
                                     'textActor' : ta})

        
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


    def _acsChoiceCallback(self):
        sliceDirection = self._getCurrentSliceDirection()
        if sliceDirection:
            selection = self._viewFrame.acsChoice.GetSelection()
            sliceDirection.resetToACS(selection)

            # once we've done this, we have to redraw
            self._viewFrame.threedRWI.Render()
    

    def _pointWidgetInteractionCallback(self, pw, evt_name):
        # we have to find pw in our list
        pwidgets = map(lambda i: i['pointWidget'], self._selectedPoints)
        if pw in pwidgets:
            idx = pwidgets.index(pw)
            # toggle the selection for this point in our list
            self._viewFrame.spointsGrid.SelectRow(idx)

            # if this is lockToSurface, lock it!
            if self._selectedPoints[idx]['lockToSurface']:
                # convert the actual pointwidget position back to display coord
                self._threedRenderer.SetWorldPoint(pw.GetPosition() + (1,))
                self._threedRenderer.WorldToDisplay()
                ex,ey,ez = self._threedRenderer.GetDisplayPoint()
                # we use a vtkPropPicker - this is supposed to make use of
                # the graphics hardware to pick rapidly
                picker = vtk.vtkPropPicker()
                if picker.PickProp(ex, ey, self._threedRenderer):
                    xyz = picker.GetPickPosition()
                    pw.SetPosition(xyz)

            # get its position and transfer it to the sphere actor that
            # we use
            pos = pw.GetPosition()
            self._selectedPoints[idx]['sphereActor'].SetPosition(pos)

            # also update the text_actor (if appropriate)
            ta = self._selectedPoints[idx]['textActor']
            if ta:
                ta.SetPosition(pos)

            inputData = self._getPrimaryInput()

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

    def _storeCursorCallback(self):
        """Call back for the store cursor button.

        Calls store cursor method on [x,y,z,v].
        """
        self._storeCursor(self._currentCursor)
        

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

    def _sliceNameChoiceCallback(self, e):
        sliceDirection = self._findSliceDirectionByName(
            self._viewFrame.sliceNameChoice.GetStringSelection())
        
        self.setCurrentSliceDirection(sliceDirection)

    def voiWidgetEndInteractionCallback(self, o, e):
        # adjust the vtkExtractVOI with the latest coords
        self._extractVOI.SetVOI(self._currentVOI)

    def inputModifiedCallback(self, o, e):
        # the data has changed, so re-render what's on the screen
        print "calling Render"
        self._viewFrame.threedRWI.Render()
        print "done calling Render"

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

        elif pickAction == 3:
            # show scalarbar for picked object
            prop, pointId = findPickedProp(obj)
            self._showScalarBarForProp(prop)

        elif pickAction == 4:
            # move the object -- for this we're going to use a special
            # vtkBoxWidget
            pass
                    
                    

