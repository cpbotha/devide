# tdObjects.py copyright (c) 2003 by Charl P. Botha <cpbotha@ieee.org>
# $Id: tdObjects.py,v 1.27 2003/08/14 11:45:07 cpbotha Exp $
# class that controls the 3-D objects list

import genUtils
reload(genUtils)
import math
import operator
import vtk
import vtkdscas
import wx
from wx.lib import colourdb

class tdObjects:
    """Class for keeping track and controlling everything to do with
    3d objects in a slice viewer.  A so-called tdObject can be a vtkPolyData
    or a vtkVolume at this stage.  The internal dict is keyed on the
    tdObject binding itself.
    """

    _objectColours = ['LIMEGREEN', 'SKYBLUE', 'PERU', 'CYAN', 
                      'GOLD',  'MAGENTA', 'GREY80',
                      'PURPLE']

    _gridCols = [('Object Name', 0), ('Colour', 120), ('Visible', 0),
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

    def addObject(self, tdObject):
        """Takes care of all the administration of adding a new 3-d object
        to the list and updating it in the list control.
        """

        if tdObject not in self._tdObjectsDict:

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

    def _attachAxis(self, sObject, twoPoints):
        """Associate the axis defined by the two world points with the
        given tdObject.
        """

        # vector from 0 to 1
        vn = map(operator.sub, twoPoints[1], twoPoints[0])
        # normalise it
        d = vtk.vtkMath.Normalize(vn)
        # calculate new lengthening vector
        v = [0.5 * d * e for e in vn]
        new0 = map(operator.sub, twoPoints[0], v)
        new1 = map(operator.add, twoPoints[1], v)
        
        # we want the actor double as long
        lineSource = vtk.vtkLineSource()
        lineSource.SetPoint1(new0)
        lineSource.SetPoint2(new1)

        tubeFilter = vtk.vtkTubeFilter()
        tubeFilter.SetNumberOfSides(8)
        tubeFilter.SetInput(lineSource.GetOutput())

        lineMapper = vtk.vtkPolyDataMapper()
        lineMapper.SetInput(tubeFilter.GetOutput())

        lineActor = vtk.vtkActor()
        lineActor.GetProperty().SetColor(1.0, 0.0, 0.0)
        lineActor.SetMapper(lineMapper)

        self._slice3dVWR._threedRenderer.AddActor(lineActor)

        self._tdObjectsDict[sObject]['axisPoints'] = twoPoints
        self._tdObjectsDict[sObject]['axisLineActor'] = lineActor

    def _axisToLineTransform(self, axisPoints, lineOrigin, lineVector):
        """Calculate the transform required to move and rotate an axis
        so that it is collinear with the given line.
        """
        
        # 2. calculate vertical distance from first axis point to line
        tp0o = map(operator.sub, axisPoints[0], lineOrigin)
        bvm = vtk.vtkMath.Dot(tp0o, lineVector) # bad vector magnitude
        bv = [bvm * e for e in lineVector] # bad vector
        # by subtracting the bad (lineVector-parallel) vector from tp0o,
        # we get only the orthogonal distance!
        od = map(operator.sub, tp0o, bv)
        # negate it
        od = [-e for e in od]

        # 3. calculate rotation around axis parallel with plane going
        #    through the first axis point

        # let's rotate
        # get axis as vector
        objectAxis = map(operator.sub, axisPoints[1], axisPoints[0])
        objectAxisM = vtk.vtkMath.Norm(objectAxis)
        rotAxis = [0.0, 0.0, 0.0]
        vtk.vtkMath.Cross(objectAxis, lineVector, rotAxis)
                    
        # calculate the new tp[1] (i.e. after the translate)
        ntp1 = map(operator.add, axisPoints[1], od)
        # relative to line origin
        ntp1o = map(operator.sub, ntp1, lineOrigin)
        # project down onto line
        bvm = vtk.vtkMath.Dot(ntp1o, lineVector)
        bv = [bvm * e for e in lineVector]
        gv = map(operator.sub, ntp1o, bv)
        
        spdM = vtk.vtkMath.Norm(gv)
                    
        # we now have y (spdM) and r (objectAxisM), so use asin
        # and convert everything to degrees
        rotAngle = math.asin(spdM / objectAxisM) / math.pi * 180

        # 4. create a homogenous transform with this translation and
        #    rotation
        
        newTransform = vtk.vtkTransform()
        newTransform.Identity()
        newTransform.PreMultiply()
        newTransform.Translate(od) # vd was the vertical translation
        tp0n = [-e for e in axisPoints[0]]
        newTransform.Translate(axisPoints[0])
        newTransform.RotateWXYZ(
            -rotAngle, rotAxis[0], rotAxis[1], rotAxis[2])
        newTransform.Translate(tp0n)

        return newTransform
        

    def _axisToLine(self, tdObject, lineOrigin, lineVector):
        objectDict = self._tdObjectsDict[tdObject]
        if 'axisPoints' not in objectDict:
            # and we do need an axis
            return

        # switch off motion as we're going to be moving things around
        # ourselves and don't want to muck about with the boxwidget
        # transform... (although we technically could)
        motionSwitched = False
        if self.getObjectMotion(tdObject):
            self._setObjectMotion(tdObject, False)
            motionSwitched = True

        # make sure lineVector is normalised
        vtk.vtkMath.Normalize(lineVector)

        # set up some convenient bindings
        axisLineActor = objectDict['axisLineActor']
        axisPoints = objectDict['axisPoints']

        # 1. okay, first determine the current world coordinates of the
        #    axis end points by transforming the stored axisPoints with
        #    the Matrix of the axisLineActor

        axisMatrix = vtk.vtkMatrix4x4()
        axisLineActor.GetMatrix(axisMatrix)

        twoPoints = []
        twoPoints.append(axisMatrix.MultiplyPoint(axisPoints[0] + (1,))[0:3])
        twoPoints.append(axisMatrix.MultiplyPoint(axisPoints[1] + (1,))[0:3])

        newTransform = self._axisToLineTransform(
            twoPoints, lineOrigin, lineVector)

        # build in theProp's existing transform
        theProp = self.findPropByObject(tdObject)
        newTransform.Concatenate(
            theProp.GetMatrix())

        # do the transform!
        for prop in (theProp, objectDict['axisLineActor']):
            prop.SetOrientation(
                newTransform.GetOrientation())
            prop.SetScale(
                newTransform.GetScale())
            prop.SetPosition(
                newTransform.GetPosition())

        if motionSwitched:
            self._setObjectMotion(tdObject, True)
            

    def _axisToPlaneTransform(self, axisPoints, planeNormal, planeOrigin):
        """Calculate transform required to rotate and move the axis defined
        by axisPoints to be coplanar with the plane defined by planeNormal
        and planeOrigin.
        """

        # 2. calculate vertical translation between the first axis point
        #    and the plane that we are going to lock to
        
        tpo = map(operator.sub, axisPoints[0], planeOrigin)
        # "vertical" distance
        vdm = vtk.vtkMath.Dot(tpo, planeNormal)
        # vector perpendicular to plane, between plane and tp[0]
        vd = [vdm * e for e in planeNormal]
        # negate it
        vd = [-e for e in vd]
        # translation == vd

        # 3. calculate rotation around axis parallel with plane going
        #    through the first axis point

        # let's rotate
        # get axis as vector
        objectAxis = map(operator.sub, axisPoints[1], axisPoints[0])
        objectAxisM = vtk.vtkMath.Norm(objectAxis)
        rotAxis = [0.0, 0.0, 0.0]
        vtk.vtkMath.Cross(objectAxis, planeNormal, rotAxis)
                    
        # calculate the new tp[1] (i.e. after the translate)
        ntp1 = map(operator.add, axisPoints[1], vd)
        # relative to plane origin
        ntp1o = map(operator.sub, ntp1, planeOrigin)
        # project down onto plane by
        # first calculating the orthogonal distance to the plane
        spdM = vtk.vtkMath.Dot(ntp1o, planeNormal)
        # multiply by planeNormal
        #spd = [spdM * e for e in ipw.GetNormal()]
        # spd is the plane-normal vector from the new axisPoints[1] to the
        # plane
                    
        # we now have y (spd) and r (objectAxisM), so use asin
        # and convert everything to degrees
        rotAngle = math.asin(spdM / objectAxisM) / math.pi * 180


        # 4. create a homogenous transform with this translation and
        #    rotation
        
        newTransform = vtk.vtkTransform()
        newTransform.Identity()
        newTransform.PreMultiply()
        newTransform.Translate(vd) # vd was the vertical translation
        tp0n = [-e for e in axisPoints[0]]
        newTransform.Translate(axisPoints[0])
        newTransform.RotateWXYZ(
            -rotAngle, rotAxis[0], rotAxis[1], rotAxis[2])
        newTransform.Translate(tp0n)

        return newTransform

    def _axisToSlice(self, tdObject, sliceDirection):
        """If tdObject has an axis, make the axis lie in the plane
        defined by sliceDirection.
        """

        if not sliceDirection._ipws:
            # we need a plane definition to latch to!
            return

        objectDict = self._tdObjectsDict[tdObject]
        if 'axisPoints' not in objectDict:
            # and we do need an axis
            return

        # switch off motion as we're going to be moving things around
        # ourselves and don't want to muck about with the boxwidget
        # transform... (although we technically could)
        motionSwitched = False
        if self.getObjectMotion(tdObject):
            self._setObjectMotion(tdObject, False)
            motionSwitched = True
        
        # set up some convenient bindings
        ipw = sliceDirection._ipws[0]
        axisLineActor = objectDict['axisLineActor']
        axisPoints = objectDict['axisPoints']

        # 1. okay, first determine the current world coordinates of the
        #    axis end points by transforming the stored axisPoints with
        #    the Matrix of the axisLineActor

        axisMatrix = vtk.vtkMatrix4x4()
        axisLineActor.GetMatrix(axisMatrix)

        twoPoints = []
        twoPoints.append(axisMatrix.MultiplyPoint(axisPoints[0] + (1,))[0:3])
        twoPoints.append(axisMatrix.MultiplyPoint(axisPoints[1] + (1,))[0:3])
        
        # calculate the transform needed to move and rotate the axis so that
        # it will be coplanar with the plane
        newTransform = self._axisToPlaneTransform(
            twoPoints, ipw.GetNormal(), ipw.GetOrigin())

        # build in theProp's existing transform
        theProp = self.findPropByObject(tdObject)
        newTransform.Concatenate(
            theProp.GetMatrix())

        # do the transform!
        for prop in (theProp, objectDict['axisLineActor']):
            prop.SetOrientation(
                newTransform.GetOrientation())
            prop.SetScale(
                newTransform.GetScale())
            prop.SetPosition(
                newTransform.GetPosition())

        if motionSwitched:
            self._setObjectMotion(tdObject, True)
        

    def _bindEvents(self):
        controlFrame = self._slice3dVWR.controlFrame

        wx.EVT_BUTTON(controlFrame, controlFrame.objectSelectAllButtonId,
                      self._handlerObjectSelectAll)

        wx.EVT_BUTTON(controlFrame, controlFrame.objectDeselectAllButtonId,
                      self._handlerObjectDeselectAll)
        
        wx.EVT_BUTTON(controlFrame, controlFrame.objectSetColourButtonId,
                      self._handlerObjectSetColour)
        
        wx.EVT_BUTTON(controlFrame, controlFrame.objectShowHideButtonId,
                      self._handlerObjectShowHide)

        wx.EVT_BUTTON(controlFrame, controlFrame.objectContourButtonId,
                      self._handlerObjectContour)

        wx.EVT_BUTTON(controlFrame, controlFrame.objectMotionButtonId,
                      self._handlerObjectMotion)

        wx.EVT_BUTTON(controlFrame, controlFrame.objectAttachAxisButtonId,
                      self._handlerObjectAttachAxis)

        wx.EVT_BUTTON(controlFrame, controlFrame.objectAxisToSliceButtonId,
                      self._handlerObjectAxisToSlice)

        wx.EVT_BUTTON(controlFrame, controlFrame.objectPlaneLockButtonId,
                      self._handlerObjectPlaneLock)

    def _detachAxis(self, tdObject):
        """Remove any object axis-related metadata and actors if tdObject
        has them.
        """

        try:
            actor = self._tdObjectsDict[tdObject]['axisLineActor']
            self._slice3dVWR._threedRenderer.RemoveActor(actor)
            del self._tdObjectsDict[tdObject]['axisPoints']
            del self._tdObjectsDict[tdObject]['axisLineActor']
        except KeyError:
            # this means the tdObject had no axis - EAFP! :)
            pass

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

    def findObjectByProp(self, prop):
        """Find the tdObject corresponding to prop.  Prop can be the vtkActor
        corresponding with a vtkPolyData tdObject or a vtkVolume tdObject.
        Whatever the case may be, this will return something that is a valid
        key in the tdObjectsDict or None
        """

        try:
            # this will succeed if prop is a vtkVolume
            return self._tdObjectsDict[prop]
        except KeyError:
            #
            for objectDict in self._tdObjectsDict.values():
                if objectDict['vtkActor'] == prop:
                    return objectDict['tdObject']

        return None
        

    def findObjectsByNames(self, objectNames):
        """Given an objectName, return a tdObject binding.
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

    def findPropByObject(self, tdObject):
        """Given a tdObject, return the corresponding prop, which could
        be a vtkActor or a vtkVolume.
        """

        t = self._tdObjectsDict[tdObject]['type']
        if t == 'vtkVolume':
            return tdObject
        if t == 'vtkPolyData':
            return self._tdObjectsDict[tdObject]['vtkActor']
        else:
            return KeyError
        

    def getPickableProps(self):
        return [o['vtkActor'] for o in self._tdObjectsDict.values()
                if 'vtkActor' in o]

    def _getSelectedObjects(self):
        """Return a list of tdObjects representing the objects that have
        been selected by the user.
        """
        
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

    def getObjectMotion(self, tdObject):
        """Returns true if motion has been activated for the tdObject.
        """
        return self._tdObjectsDict[tdObject]['motion']

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

    def _handlerObjectAttachAxis(self, event):
        """The user should have selected at least two points and an object.
        This will record the axis formed by the two selected points as the
        object axis.  If no points are selected, and an axis already exists,
        we detach the axis.
        """

        worldPoints = self._slice3dVWR.selectedPoints.getSelectedWorldPoints()
        sObjects = self._getSelectedObjects()
        if len(worldPoints) >= 2 and sObjects:
            for sObject in sObjects:
                # detach any previous stuff
                self._detachAxis(sObject)
                # the user asked for it, so we're doing all of 'em
                self._attachAxis(sObject, worldPoints[0:2])

            if sObjects:
                self._slice3dVWR.render3D()
                
        elif not worldPoints and sObjects:
            # this means the user might want to remove all axes from
            # the sObjects
            md = wx.MessageDialog(
                self._slice3dVWR.controlFrame,
                "Are you sure you want to REMOVE axes "
                "from all selected objects?",
                "Confirm axis removal",
                wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
            if md.ShowModal() == wx.ID_YES:
                for sObject in sObjects:
                    self._detachAxis(sObject)

                if sObjects:
                    self._slice3dVWR.render3D()

        else:
            md = wx.MessageDialog(
                self._slice3dVWR.controlFrame,
                "To attach an axis to an object, you need to select two "
                "points and an object.",
                "Information",
                wx.OK | wx.ICON_INFORMATION)
            md.ShowModal()

    def _handlerObjectAxisToSlice(self, event):
        #
        sObjects = self._getSelectedObjects()
        sSliceDirections = self._slice3dVWR.sliceDirections.\
                           getSelectedSliceDirections()

        if not sSliceDirections:
            md = wx.MessageDialog(self._slice3dVWR.controlFrame,
                                  "Select at least one slice before "
                                  "using AxisToSlice.",
                                  "Information",
                                  wx.OK | wx.ICON_INFORMATION)
            md.ShowModal()
            return

        if not sObjects:
            md = wx.MessageDialog(self._slice3dVWR.controlFrame,
                                  "Select at least on object before "
                                  "using AxisToSlice.",
                                  "Information",
                                  wx.OK | wx.ICON_INFORMATION)
            md.ShowModal()
            return

        for sObject in sObjects:
            if len(sSliceDirections) == 1:
                # align axis with plane
                self._axisToSlice(sObject, sSliceDirections[0])
            elif len(sSliceDirections) == 2:
                # align axis with intersection of two planes (ouch)
                try:
                    pn0 = sSliceDirections[0]._ipws[0].GetNormal()
                    po0 = sSliceDirections[0]._ipws[0].GetOrigin()
                    pn1 = sSliceDirections[1]._ipws[0].GetNormal()
                    po1 = sSliceDirections[1]._ipws[0].GetOrigin()
                except IndexError:
                    md = wx.MessageDialog(self._slice3dVWR.controlFrame,
                                          "The slices you have selected "
                                          "contain no data.",
                                          "Information",
                                          wx.OK | wx.ICON_INFORMATION)
                    md.ShowModal()
                    return

                try:
                    lineOrigin, lineVector = genUtils.planePlaneIntersection(
                        pn0, po0, pn1, po1)
                except ValueError, msg:
                    md = wx.MessageDialog(self._slice3dVWR.controlFrame,
                                          "The two slices you have selected "
                                          "are parallel, no intersection "
                                          "can be calculated.",
                                          "Information",
                                          wx.OK | wx.ICON_INFORMATION)
                    md.ShowModal()
                    return
                    
                # finally send it to the line
                self._axisToLine(sObject, lineOrigin, lineVector)
                
            else:
                md = wx.MessageDialog(self._slice3dVWR.controlFrame,
                                      "You have selected more than two "
                                      "slices. "
                                      "I am not sure what I should think "
                                      "about this.",
                                      "Information",
                                      wx.OK | wx.ICON_INFORMATION)
                md.ShowModal()
                return
        
        if sObjects:
            self._slice3dVWR.render3D()

    def _handlerObjectPlaneLock(self, event):
        """Lock the selected objects to the selected planes.  This will
        constrain future motion to the planes as they are currently defined.
        If no planes are selected, the system will lift the locking.
        """

        sObjects = self._getSelectedObjects()
        sSliceDirections = self._slice3dVWR.sliceDirections.\
                           getSelectedSliceDirections()

        if sObjects and sSliceDirections:
            for sObject in sObjects:
                # first unlock from any previous locks
                self._unlockObjectFromPlanes(sObject)
                for sliceDirection in sSliceDirections:
                    self._lockObjectToPlane(sObject, sliceDirection)

        elif sObjects:
            md = wx.MessageDialog(
                self._slice3dVWR.controlFrame,
                "Are you sure you want to UNLOCK the selected objects "
                "from all slices?",
                "Confirm Object Unlock",
                wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
            
            if md.ShowModal() == wx.ID_YES:
                for sObject in sObjects:
                    self._unlockObjectFromPlanes(sObject)

        else:
            md = wx.MessageDialog(
                self._slice3dVWR.controlFrame,
                "To lock an object to plane, you have to select at least "
                "one object and one slice.",
                "Information",
                wx.OK | wx.ICON_INFORMATION)
            
            md.ShowModal()

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

    def _lockObjectToPlane(self, tdObject, sliceDirection):
        """Set it up so that motion of tdObject will be constrained to the
        current plane equation of the given sliceDirection.
        """

        if not sliceDirection._ipws:
            # we need some kind of plane equation!
            return

        newPlaneNormal = sliceDirection._ipws[0].GetNormal()

        try:
            self._tdObjectsDict[tdObject]['motionConstraintVectors'].append(
                newPlaneNormal)
        except KeyError:
            self._tdObjectsDict[tdObject][
                'motionConstraintVectors'] = [newPlaneNormal]

        # if a motionBoxWidget already exists, make sure it knows about the
        # new constraints
        if 'motionBoxWidget' in self._tdObjectsDict[tdObject]:
            self._setupMotionConstraints(
                self._tdObjectsDict[tdObject]['motionBoxWidget'],
                tdObject)

    def _observerMotionBoxWidgetEndInteraction(self, eventObject, eventType):
        # make sure the transform is up to date
        self._observerMotionBoxWidgetInteraction(eventObject, eventType)

        self._postObjectMotionSync(eventObject.GetProp3D())
        

    def _observerMotionBoxWidgetInteraction(self, eventObject, eventType):
        bwTransform = vtk.vtkTransform()
        eventObject.GetTransform(bwTransform)
        
        eventObject.GetProp3D().SetUserTransform(bwTransform)

    def _postObjectMotionSync(self, prop):
        # FIXME: continue here
        
        # and update the contours after we're done moving things around
        self._slice3dVWR.sliceDirections.syncContoursToObjectViaProp(prop)

        # THIS IS BROKEN!
        
        # now make sure that the object axis (if any) is also aligned
        # find the tdObject corresponding to the prop
        tdObject = self.findObjectByProp(prop)
        try:
            # if there's a line, move it too!
            axisLineActor = self._tdObjectsDict[tdObject]['axisLineActor']
            bwTransform = vtk.vtkTransform()
            eventObject.GetTransform(bwTransform)
            axisLineActor.SetUserTransform(bwTransform)
        except KeyError:
            pass
        
        

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

            try:
                # if there was a axisLineActor, remove that as well
                lineActor = self._tdObjectsDict[tdObject]['axisLineActor']
                self._slice3dVWR._threedRenderer.RemoveActor(lineActor)
            except KeyError:
                pass
            
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
                genUtils.setGridCellYesNo(
                    self._grid,gridRow, self._gridVisibleCol, visible)

    def _setObjectContouring(self, tdObject, contour):
        if self._tdObjectsDict.has_key(tdObject):
            objectDict = self._tdObjectsDict[tdObject]

            # in our own dict
            objectDict['contour'] = bool(contour)

            if objectDict['type'] == 'vtkPolyData':
                # in the scene
                if contour:
                    self._slice3dVWR.sliceDirections.addContourObject(
                        tdObject, objectDict['vtkActor'])
                else:
                    self._slice3dVWR.sliceDirections.removeContourObject(
                        tdObject)

            # in the grid
            gridRow = self.findGridRowByName(objectDict['objectName'])
            if gridRow >= 0:
                if objectDict['type'] == 'vtkPolyData':
                    genUtils.setGridCellYesNo(
                        self._grid, gridRow, self._gridContourCol, contour)

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
                # the balls only confuse us!
                bw.HandlesOff()
                # without the balls, the outlines aren't needed either
                bw.OutlineCursorWiresOff()
                bw.SetInteractor(self._slice3dVWR.threedFrame.threedRWI)
                # also "flatten" the actor (i.e. integrate its UserTransform)
                genUtils.flattenProp3D(objectDict['vtkActor'])
                # and the axis, if any
                try:
                    genUtils.flattenProp3D(objectDict['axisLineActor'])
                except KeyError:
                    pass
                                          
                bw.SetProp3D(objectDict['vtkActor'])
                
                bw.SetPlaceFactor(1.0)
                bw.PlaceWidget()
                bw.On()

                bw.AddObserver('EndInteractionEvent',
                               self._observerMotionBoxWidgetEndInteraction)
                bw.AddObserver('InteractionEvent',
                               self._observerMotionBoxWidgetInteraction)


                # FIXME: continue here!
#                 try:
#                     ipw = self._slice3dVWR._sliceDirections[0]._ipws[0]
#                 except:
#                     # no plane, so we don't do anything
#                     pass
#                 else:
#                     bw.ConstrainToPlaneOn()
#                     bw.SetConstrainPlaneNormal(ipw.GetNormal())

                self._setupMotionConstraints(bw, tdObject)
                

            else:
                if 'motionBoxWidget' in objectDict and \
                   objectDict['motionBoxWidget']:
                    try:
                        # let's flatten the prop again (if there is one)
                        genUtils.flattenProp3D(objectDict['vtkActor'])
                        # and flatten the axis (if any)
                        genUtils.flattenProp3D(objectDict['axisLineActor'])
                    except KeyError:
                        pass
                        
                    objectDict['motionBoxWidget'].Off()
                    objectDict['motionBoxWidget'].SetInteractor(None)
                    objectDict['motionBoxWidget'] = None
            
            # finally in the grid
            gridRow = self.findGridRowByName(objectDict['objectName'])
            if gridRow >= 0:
                if objectDict['type'] == 'vtkPolyData':
                    genUtils.setGridCellYesNo(
                        self._grid, gridRow, self._gridMotionCol, motion)

                else:
                    self._grid.SetCellValue(gridRow, self._gridMotionCol,
                                            'N/A')

    def _setupMotionConstraints(self, boxWidget, tdObject):
        """Configure boxWidget (a vtkBoxWidgetConstrained) to constrain as
        specified by the motionConstraintVectors member in the objectDict
        corresponding to tdObject.

        If there are more than two motionConstraintVectors, only the first
        two will be used.
        """

        try:
            mCV = self._tdObjectsDict[tdObject]['motionConstraintVectors']
        except KeyError:
            mCV = None

        if not mCV:
            # i.e. this is an empty vector (or we deliberately set it to None)
            # either way, we have to disable all constraints
            boxWidget.SetConstraintType(0)
            
        elif len(mCV) == 1:
            # plane constraint (i.e. we have only a single plane normal)
            boxWidget.SetConstraintType(2) # plane
            boxWidget.SetConstraintVector(mCV[0])
            
        else:
            # line constraint (intersection of two planes that have been
            # stored as plane normals
            boxWidget.SetConstraintType(1)
            # now determine the constraint line by calculating the cross
            # product of the two plane normals
            lineVector = [0.0, 0.0, 0.0]
            vtk.vtkMath.Cross(mCV[0], mCV[1], lineVector)
            # and tell the boxWidget about this!
            boxWidget.SetConstraintVector(lineVector)

    def _tdObjectModifiedCallback(self, o, e):
        self._slice3dVWR.render3D()

    def _unlockObjectFromPlanes(self, tdObject):
        """Make sure that there are no plane constraints on the motion
        of the given tdObject.
        """

        try:
            del self._tdObjectsDict[tdObject]['motionConstraintVectors'][:]
        except KeyError:
            pass

        # if a motionBoxWidget already exists, make sure it knows about
        # the changes
        if 'motionBoxWidget' in self._tdObjectsDict[tdObject]:
            self._setupMotionConstraints(
                self._tdObjectsDict[tdObject]['motionBoxWidget'],
                tdObject)
