# tdObjects.py copyright (c) 2003 by Charl P. Botha <cpbotha@ieee.org>
# $Id: tdObjects.py,v 1.9 2003/06/30 12:07:47 cpbotha Exp $
# class that controls the 3-D objects list

import math
import operator
import vtk
import vtkdscas
import wx
from wx.lib import colourdb

class tdObjects:

    _objectColours = ['LIMEGREEN', 'SKYBLUE', 'PERU', 'CYAN', 
                      'GOLD',  'MAGENTA', 'GREY80',
                      'PURPLE']

    _gridCols = [('Object Name', 0), ('Colour', 150), ('Visible', 0),
                 ('Contour', 0), ('Motion', 0)]
    
    _gridNameCol = 0
    _gridColourCol = 1
    _gridVisibleCol = 2
    _gridContourCol = 3
    _gridMotionCol = 4

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

        wx.EVT_BUTTON(svViewFrame, svViewFrame.objectSelectAllButtonId,
                      self._handlerObjectSelectAll)

        wx.EVT_BUTTON(svViewFrame, svViewFrame.objectDeselectAllButtonId,
                      self._handlerObjectDeselectAll)
        
        wx.EVT_BUTTON(svViewFrame, svViewFrame.objectSetColourButtonId,
                      self._handlerObjectSetColour)
        
        wx.EVT_BUTTON(svViewFrame, svViewFrame.objectShowHideButtonId,
                      self._handlerObjectShowHide)

        wx.EVT_BUTTON(svViewFrame, svViewFrame.objectContourButtonId,
                      self._handlerObjectContour)

        wx.EVT_BUTTON(svViewFrame, svViewFrame.objectMotionButtonId,
                      self._handlerObjectMotion)

        wx.EVT_BUTTON(svViewFrame, svViewFrame.objectAxisToSliceButtonId,
                      self._handlerObjectAxisToSlice)

    def _getSelectedObjects(self):
        objectNames = []        
        selectedRows = self._grid.GetSelectedRows()
        for sRow in selectedRows:
            objectNames.append(
                self._grid.GetCellValue(sRow, self._gridNameCol)
                )

        objs = self.findObjectsByNames(objectNames)
        return objs

    def getContourObjects(self):
        """Returns a list of objects that have contouring activated.
        """
        return [o['tdObject'] for o in self._tdObjectsDict.values()
                if o['contour']]

    def getObjectColour(self, tdObject):
        """Given tdObject, this will return that object's current colour
        in the scene.  If the tdObject doesn't exist in our list, it gets
        green by default.
        """
        
        try:
            return self._tdObjectsDict[tdObject]['colour']
        except:
            return (0.0, 1.0, 0.0)

    def _handlerObjectSelectAll(self, event):
        for row in range(self._grid.GetNumberRows()):
            self._grid.SelectRow(row, True)

    def _handlerObjectDeselectAll(self, event):
        self._grid.ClearSelection()

    def _handlerObjectContour(self, event):
        objs = self._getSelectedObjects()

        for obj in objs:
            contour = self._tdObjectsDict[obj]['contour']
            self._setObjectContouring(obj, not contour)

        if objs:
            self._slice3dVWR.render3D()

    def _handlerObjectSetColour(self, event):
        objs = self._getSelectedObjects()
        
        if objs:
            self._slice3dVWR.setColourDialogColour(
                self._tdObjectsDict[objs[0]]['colour'])
                
            dColour = self._slice3dVWR.getColourDialogColour()
            if dColour:
                for obj in objs:
                    self._setObjectColour(obj, dColour)

        if objs:
            self._slice3dVWR.render3D()
                    

    def _handlerObjectShowHide(self, event):
        objs = self._getSelectedObjects()

        for obj in objs:
            visible = self._tdObjectsDict[obj]['visible']
            self._setObjectVisibility(obj, not visible)

        if objs:
            self._slice3dVWR.render3D()

    def _handlerObjectMotion(self, event):
        objs = self._getSelectedObjects()

        for obj in objs:
            motion = self._tdObjectsDict[obj]['motion']
            self._setObjectMotion(obj, not motion)

        if objs:
            self._slice3dVWR.render3D()

    def _handlerObjectAxisToSlice(self, event):
        # first find two selected points from the selected points list
        selPoints = self._slice3dVWR._viewFrame.spointsGrid.GetSelectedRows()
        sliceDirection = self._slice3dVWR._getCurrentSliceDirection()
        
        if len(selPoints) >= 2 and sliceDirection and sliceDirection._ipws:
            tp = [self._slice3dVWR._selectedPoints[idx]['world']
                  for idx in selPoints[:2]]
            ipw = sliceDirection._ipws[0]

            objs = self._getSelectedObjects()
            for obj in objs:
                objectDict = self._tdObjectsDict[obj]
                if objectDict['type'] == 'vtkPolyData':
                    newTransform = vtk.vtkTransform()
                    newTransform.Identity()
                    newTransform.PreMultiply()
                    cm = objectDict['vtkActor'].GetMatrix()
                    newTransform.Concatenate(cm)

                    po = ipw.GetOrigin()
                    tpo = map(operator.sub, tp[0], po)
                    # "vertical" distance
                    vdm = vtk.vtkMath.Dot(tpo, ipw.GetNormal())
                    vd = [vdm * e for e in ipw.GetNormal()]
                    # negate it
                    vd = [-e for e in vd]
                    # and abuse the transform
                    newTransform.Translate(vd)

                    # let's rotate
                    # get axis as vector
                    objectAxis = map(operator.sub, tp[1], tp[0])
                    objectAxisM = vtk.vtkMath.Norm(objectAxis)
                    rotAxis = [0.0, 0.0, 0.0]
                    vtk.vtkMath.Cross(objectAxis, ipw.GetNormal(), rotAxis)
                    # calculate the new tp[1] (i.e. after the translate)
                    ntp1 = map(operator.sub, tp[1], vd)
                    ntp1m = vtk.vtkMath.Norm(ntp1)
                    # we now have y (ntp1m) and r (objectAxisM), so use asin
                    # and convert everything to degrees
                    rotAngle = math.asin(ntp1m / objectAxisM) / math.pi * 180

                    #newTransform.RotateWXYZ(rotAngle,
                    #                        rotAxis[0], rotAxis[1], rotAxis[2])

                    
                    ntp0 = map(operator.sub, tp[0], vd)
                    objectDict['vtkActor'].SetOrigin(ntp0)
                    objectDict['vtkActor'].SetOrientation(
                        newTransform.GetOrientation())
                    objectDict['vtkActor'].SetScale(
                        newTransform.GetScale())
                    objectDict['vtkActor'].SetPosition(
                        newTransform.GetPosition())
                    
            # closes: for obj in objs:
            self._slice3dVWR.render3D()

        else:
            wxLogMessage("You have to select two points and a slice.")
            
    def _initialiseGrid(self):
        """Setup the object listCtrl from scratch, mmmkay?
        """

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
            colour = wx.TheColourDatabase.FindColour(colourName).asTuple()
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
            self._grid.SetCellValue(nrGridRows, self._gridNameCol, objectName)
            #self._grid.SetCellValue(nrGridRows, self._gridColourCol,
            #                        colourName)
            #self._grid.SetCellValue(nrGridRows, self._gridVisibleCol, 'Yes')
            
            # store the name
            self._tdObjectsDict[tdObject]['objectName'] = objectName
            # and store the colour
            self._setObjectColour(tdObject, nColour)
            # and the visibility
            self._setObjectVisibility(tdObject, True)
            # and the contouring
            self._setObjectContouring(tdObject, False)
            # and the motion
            self._setObjectMotion(tdObject, False)

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

    def findObjectByActor(self, actor):
        for oi in objectsDict.items():
            if oi[1]['type'] == vtkPolyData and \
               oi[1]['vtkActor'] == actor:
                return oi[0]

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

    def _observerMotionBoxWidgetEndInteraction(self, eventObject, eventType):
        
        bwTransform = vtk.vtkTransform()
        #tp = eventObject.GetProp3D()
        #eventObject.SetProp3D(None)
        eventObject.GetTransform(bwTransform)
        #eventObject.SetProp3D(tp)

        pd = vtk.vtkPolyData()
        eventObject.GetPolyData(pd)
        c = pd.GetPoints().GetData().GetTuple3(14)
        mc = [-e for e in c]        
        #c = eventObject.GetProp3D().GetCenter()
        #p = eventObject.GetProp3D().GetPosition()
        #o = map(operator.sub, p, c)

        # get the current matrix
        cm = eventObject.GetProp3D().GetMatrix()
        # the current prop matrix should be applied before the
        # new boxwidget one
        bwTransform.PreMultiply()

        bwTransform.Concatenate(cm)

        #eventObject.GetProp3D().SetOrigin(c)        

        eventObject.GetProp3D().SetOrientation(bwTransform.GetOrientation())
        eventObject.GetProp3D().SetPosition(bwTransform.GetPosition())
        eventObject.GetProp3D().SetScale(bwTransform.GetScale())
        
        eventObject.PlaceWidget()

        # and update the contours after we've moved things around
        for sd in self._slice3dVWR._sliceDirections:
            sd.syncContourToObjectViaProp(eventObject.GetProp3D())

    def _observerMotionBoxWidgetInteraction(
        self, eventObject, eventType, objectDict):
        # if the object has been constrained, we do our thing here

        # for now, we just use the first frikking plane, mmmkay?
        try:
            ipw = self._slice3dVWR._sliceDirections[0]._ipws[0]
        except:
            # no plane, so we don't do anything
            return

        planeNormal = ipw.GetNormal()
        prevCentre = objectDict['motionBoxWidgetPrevCentre']

        pd = vtk.vtkPolyData()
        eventObject.GetPolyData(pd)
        curCentre = pd.GetPoints().GetData().GetTuple3(14)

        # now calculate motion vector
        mv = map(operator.sub, curCentre, prevCentre)
        # calculate "bad" component
        bc = vtk.vtkMath.Dot(planeNormal, mv)
        bc = [bc * e for e in planeNormal]
        # because this is a hack and a kludge, we're just going to translate
        # the boxwidget with the negative "bad" component
        nbc = [-e for e in bc]

        print mv
        print nbc

        trfm = vtk.vtkTransform()
        eventObject.GetTransform(trfm)
        #trfm.PostMultiply()
        #trfm.Translate(nbc)
        eventObject.SetTransform(trfm)

    def removeObject(self, tdObject):
        if not self._tdObjectsDict.has_key(tdObject):
            raise Exception, 'Attempt to remove non-existent tdObject'

        # this will take care of motion boxes and the like
        self._setObjectMotion(tdObject, False)

        oType = self._tdObjectsDict[tdObject]['type']
        if oType == 'vtkVolume':
            self._slice3dVWR._threedRenderer.RemoveVolume(tdObject)
            self._slice3dVWR.render3D()

        elif oType == 'vtkPolyData':
            # remove all contours due to this object
            self._setObjectContouring(tdObject, False)
            
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
                    colour = wx.Colour(r,g,b)
                    self._grid.SetCellBackgroundColour(
                        row, self._gridColourCol, colour)
                    
                    # also search for the name
                    cName = wx.TheColourDatabase.FindName(colour)
                    if not cName:
                        cName = 'USER DEFINED'

                    self._grid.SetCellValue(row, self._gridColourCol, cName)

    def _setObjectVisibility(self, tdObject, visible):
        if self._tdObjectsDict.has_key(tdObject):
            objectDict = self._tdObjectsDict[tdObject]

            # in our own dict
            objectDict['visible'] = bool(visible)
            
            # in the scene
            if objectDict['type'] == 'vtkVolume':
                tdObject.SetVisibility(bool(visible))
            elif objectDict['type'] == 'vtkPolyData':
                objectDict['vtkActor'].SetVisibility(bool(visible))
            else:
                pass

            # finally in the grid
            gridRow = self.findGridRowByName(objectDict['objectName'])
            if gridRow >= 0:
                self._grid.SetCellValue(gridRow, self._gridVisibleCol,
                                        ['No', 'Yes'][bool(visible)])

    def _setObjectContouring(self, tdObject, contour):
        if self._tdObjectsDict.has_key(tdObject):
            objectDict = self._tdObjectsDict[tdObject]

            # in our own dict
            objectDict['contour'] = bool(contour)

            if objectDict['type'] == 'vtkPolyData':
                # in the scene
                for sd in self._slice3dVWR._sliceDirections:
                    if contour:
                        sd.addContourObject(tdObject, objectDict['vtkActor'])
                    else:
                        sd.removeContourObject(tdObject)

            # in the grid
            gridRow = self.findGridRowByName(objectDict['objectName'])
            if gridRow >= 0:
                if objectDict['type'] == 'vtkPolyData':
                    self._grid.SetCellValue(gridRow, self._gridContourCol,
                                            ['No', 'Yes'][bool(contour)])
                else:
                    self._grid.SetCellValue(gridRow, self._gridContourCol,
                                            'N/A')


    def _setObjectMotion(self, tdObject, motion):
        if tdObject in self._tdObjectsDict:
            objectDict = self._tdObjectsDict[tdObject]

            # in our own dict
            objectDict['motion'] = bool(motion)

            # tell the sliceViewer that this is movable
            # FIXME WORKAROUND: this will ALWAYS set motion to True, even
            # when motion is being deactivated... this is a quick workaround
            # for the superbly broken vtkBoxWidget.  Thanks guys.
            if objectDict['type'] == 'vtkPolyData':
                self._slice3dVWR.setPropMotion(objectDict['vtkActor'], True)

            # setup our frikking motionBoxWidget, mmmkay?
            if motion:
                if 'motionBoxWidget' in objectDict and \
                   objectDict['motionBoxWidget']:
                    # take care of the old one
                    objectDict['motionBoxWidget'].Off()
                    objectDict['motionBoxWidget'].SetInteractor(None)
                    objectDict['motionBoxWidget'] = None

                # we like to do it anew
                objectDict['motionBoxWidget'] = vtkdscas.\
                                                vtkBoxWidgetConstrained()
                bw = objectDict['motionBoxWidget']
                    
                # we don't want the user to scale, only move and rotate
                bw.ScalingEnabledOff()
                # FIXME WORKAROUND: the vtkBoxWidget is BROKEN
                #bw.RotationEnabledOff()
                bw.SetInteractor(self._slice3dVWR._viewFrame.threedRWI)
                bw.SetProp3D(objectDict['vtkActor'])
                bw.SetPlaceFactor(1.0)
                bw.PlaceWidget()
                bw.On()

                bw.AddObserver('EndInteractionEvent',
                               self._observerMotionBoxWidgetEndInteraction)

                try:
                    ipw = self._slice3dVWR._sliceDirections[0]._ipws[0]
                except:
                    # no plane, so we don't do anything
                    pass
                else:
                    bw.ConstrainToPlaneOn()
                    bw.SetConstrainPlaneNormal(ipw.GetNormal())
                

            else:
                if 'motionBoxWidget' in objectDict and \
                   objectDict['motionBoxWidget']:
                    objectDict['motionBoxWidget'].Off()
                    objectDict['motionBoxWidget'].SetInteractor(None)
                    objectDict['motionBoxWidget'] = None
            
            # finally in the grid
            gridRow = self.findGridRowByName(objectDict['objectName'])
            if gridRow >= 0:
                if objectDict['type'] == 'vtkPolyData':
                    self._grid.SetCellValue(gridRow, self._gridMotionCol,
                                            ['No', 'Yes'][bool(motion)])
                else:
                    self._grid.SetCellValue(gridRow, self._gridMotionCol,
                                            'N/A')
                    

    def _tdObjectModifiedCallback(self, o, e):
        self._slice3dVWR.render3D()

