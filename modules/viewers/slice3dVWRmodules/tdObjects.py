# tdObjects.py copyright (c) 2003 by Charl P. Botha <cpbotha@ieee.org>
# $Id$
# class that controls the 3-D objects list

import genUtils
reload(genUtils)
import math
import module_kits
from module_kits.vtk_kit import misc
from modules.viewers.slice3dVWRmodules.shared import s3dcGridMixin
import operator
import vtk
import vtkdevide
import wx
import wx.grid
from wx.lib import colourdb

class tdObjects(s3dcGridMixin):
    """Class for keeping track and controlling everything to do with
    3d objects in a slice viewer.  A so-called tdObject can be a vtkPolyData
    or a vtkVolume at this stage.  The internal dict is keyed on the
    tdObject binding itself.
    """

    _objectColours = ['LIMEGREEN', 'SKYBLUE', 'PERU', 'CYAN', 
                      'GOLD',  'MAGENTA', 'GREY80',
                      'PURPLE']

    _gridCols = [('Object Name', 0), ('Colour', 110), ('Visible', 0),
                 ('Contour', 0), ('Motion', 0), ('Scalars',0)]
    
    _gridNameCol = 0
    _gridColourCol = 1
    _gridVisibleCol = 2
    _gridContourCol = 3
    _gridMotionCol = 4
    _gridScalarVisibilityCol = 5

    def __init__(self, slice3dVWRThingy, grid):
        self._tdObjectsDict = {}
        self._objectId = 0
        
        self.slice3dVWR = slice3dVWRThingy
        self._grid = grid
        self._initialiseGrid()
        self._bindEvents()

        # fill out our drop-down menu
        self._disableMenuItems = self._appendGridCommandsToMenu(
            self.slice3dVWR.controlFrame.objectsMenu,
            self.slice3dVWR.controlFrame, disable=True)


        # some GUI events that have to do with the objects list
        wx.EVT_BUTTON(self.slice3dVWR.objectAnimationFrame,
                      self.slice3dVWR.objectAnimationFrame.resetButtonId,
                      self._handlerObjectAnimationReset)

        wx.EVT_SLIDER(self.slice3dVWR.objectAnimationFrame,
                      self.slice3dVWR.objectAnimationFrame.frameSliderId,
                      self._handlerObjectAnimationSlider)
        

        # this will fix up wxTheColourDatabase
        colourdb.updateColourDB()

    def close(self):
        self._tdObjectsDict.clear()
        self.slice3dVWR = None
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

            # we'll need this later (when we decide about scalar vis)
            scalarsName = None
            
            # now actually create the necessary thingies and add the object
            # to the scene
            if hasattr(tdObject, 'GetClassName') and \
               callable(tdObject.GetClassName):

                if tdObject.GetClassName() == 'vtkVolume':
                    self.slice3dVWR._threedRenderer.AddVolume(tdObject)
                    self._tdObjectsDict[tdObject] = {'tdObject' : tdObject,
                                                     'type' : 'vtkVolume'}

                    # we have to test this here already... if there's
                    # a VTK error (for instance volume rendering the wrong
                    # type) we remove the volume and re-raise the exception
                    # the calling code will act as if no successful add
                    # was performed, thus feeding back the error
                    try:
                        self.slice3dVWR._threedRenderer.ResetCamera()
                        self.slice3dVWR.render3D()
                    except RuntimeError:
                        self.slice3dVWR._threedRenderer.RemoveVolume(tdObject)
                        raise

                elif tdObject.GetClassName() == 'vtkPolyData':
                    mapper = vtk.vtkPolyDataMapper()
                    mapper.ImmediateModeRenderingOn()
                    mapper.SetInput(tdObject)
                    actor = vtk.vtkActor()
                    actor.SetMapper(mapper)

                    #actor.GetProperty().LoadMaterial('GLSLTwisted')
                    #actor.GetProperty().ShadingOn()
                    #actor.GetProperty().AddShaderVariableFloat('Rate', 1.0)

                    # now we are going to set the PERFECT material
                    p = actor.GetProperty()

                    # i prefer flat shading, okay?
                    p.SetInterpolationToFlat()

                    # Ka, background lighting coefficient
                    p.SetAmbient(0.1)
                    # light reflectance
                    p.SetDiffuse(0.6)
                    # the higher Ks, the more intense the highlights
                    p.SetSpecular(0.4)
                    # the higher the power, the more localised the
                    # highlights
                    p.SetSpecularPower(100)

                    self.slice3dVWR._threedRenderer.AddActor(actor)
                    self._tdObjectsDict[tdObject] = {'tdObject' : tdObject,
                                                     'type' : 'vtkPolyData',
                                                     'vtkActor' : actor}

                    # to get the name of the scalars we need to do this.
                    tdObject.Update()
                
                    if tdObject.GetPointData().GetScalars():
                        scalarsName = tdObject.GetPointData().GetScalars().\
                                      GetName()
                    else:
                        scalarsName = None

                    if scalarsName:
                        mapper.SetScalarRange(tdObject.GetScalarRange())

                    #mapper.ScalarVisibilityOff()
                
#                     if sname and sname.lower().find("curvature") >= 0:
#                         # if the active scalars have "curvature" somewhere in
#                         # their name, activate flat shading and scalar vis
#                         property = actor.GetProperty()
#                         property.SetInterpolationToFlat()
#                         mapper.ScalarVisibilityOn()
                    
#                     else:
#                         # the user can switch this back on if she really
#                         # wants it
#                         # we switch it off as we mostly work with isosurfaces
#                         mapper.ScalarVisibilityOff()
                
                else:
                    raise Exception, 'Non-handled tdObject type'

            else:
                # the object has no GetClassName that's callable
                raise Exception, 'tdObject has no GetClassName()'

            nrGridRows = self._grid.GetNumberRows()
            self._grid.AppendRows()
            self._grid.SetCellValue(nrGridRows, self._gridNameCol, objectName)

            # set the relevant cells up for Boolean
            for col in [self._gridVisibleCol, self._gridContourCol,
                        self._gridMotionCol, self._gridScalarVisibilityCol]:
                self._grid.SetCellRenderer(nrGridRows, col,
                                           wx.grid.GridCellBoolRenderer())
                self._grid.SetCellAlignment(nrGridRows, col,
                                            wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)
            
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
            # scalar visibility
            if scalarsName:
                self._setObjectScalarVisibility(tdObject, True)
            else:
                self._setObjectScalarVisibility(tdObject, False)

            
        # ends 
        else:
            raise Exception, 'Attempt to add same object twice.'

    def updateObject(self, prevObject, newObject):
        """Method used to update new data on a new connection.

        When the moduleManager transfers data, it simply calls set_input()
        with a non-None inputStream on an already non-None connection.  This
        function will take the necessary steps to update just the object and
        keep everything else as is.

        @param prevObject: the previous object binding, will be used to remove
        if the binding has changed.
        @param newObject: the new object binding.
        """

        if newObject.GetClassName() == 'vtkVolume':
            # remove old object from renderer
            self.slice3dVWR._threedRenderer.RemoveVolume(prevObject)
            # store the old object dict
            objectDict = self._tdObjectsDict[prevObject]
            # remove it from our list
            del self._tdObjectsDict[prevObject]

            # add the object to the renderer
            self.slice3dVWR._threedRenderer.AddVolume(newObject)
            # modify the stored old object dict with the new object
            objectDict['tdObject'] = newObject
            # and store it in our list!
            self._tdObjectsDict[newObject] = objectDict
        
        elif newObject.GetClassName() == 'vtkPolyData':
            objectDict = self._tdObjectsDict[prevObject]
            del self._tdObjectsDict[prevObject]

            # BUG #67 is HERE!  only the mapper for the object itself is
            # changed, but not for the tube object.
            
            # record the new object ###################################
            objectDict['tdObject'] = newObject
            mapper = objectDict['vtkActor'].GetMapper()
            mapper.SetInput(newObject)
            self._tdObjectsDict[newObject] = objectDict

            # set the new scalar range ################################
            if newObject.GetPointData().GetScalars():
                scalarsName = newObject.GetPointData().GetScalars().\
                              GetName()
            else:
                scalarsName = None
                
            if scalarsName:
                mapper.SetScalarRange(newObject.GetScalarRange())
            

            

    def _appendGridCommandsToMenu(self, menu, eventWidget, disable=True):
        """Appends the points grid commands to a menu.  This can be used
        to build up the context menu or the drop-down one.
        """

        commandsTuple = [
            ('Select &All', 'Select all objects',
             self._handlerObjectSelectAll, False),
            ('D&Eselect All', 'Deselect all objects',
             self._handlerObjectDeselectAll, False),
            ('---',),
            ('&Show', 'Show all selected objects',
             self._handlerObjectShow, True),
            ('&Hide', 'Hide all selected objects',
             self._handlerObjectHide, True),
            ('&Motion ON +', 'Enable motion for selected objects',
             self._handlerObjectMotionOn, True),
            ('M&otion OFF', 'Disable motion for selected objects',
             self._handlerObjectMotionOff, True),
            ('Set &Colour',
             'Change colour of selected objects',
             self._handlerObjectSetColour, True),
            ('Set O&pacity',
             'Change opacity of selected objects',
             self._handlerObjectSetOpacity, True),
            ('Con&touring On +',
             'Activate contouring for all selected objects',
             self._handlerObjectContourOn, True),
            ('Conto&uring Off',
             'Deactivate contouring for all selected objects',
             self._handlerObjectContourOff, True),
            ('Scalar Visibility On +',
             'Activate scalar visibility for all selected objects',
             self._handlerObjectScalarVisibilityOn, True),
            ('Scalar Visibility Off',
             'Deactivate scalar visibility for all selected objects',
             self._handlerObjectScalarVisibilityOff, True),            
            ('---',), # important!  one-element tuple...
            ('Attach A&xis',
             'Attach axis to all selected objects',
             self._handlerObjectAttachAxis, True),
            ('Mo&ve Axis to Slice',
             'Move the object (via its axis) to the selected slices',
             self._handlerObjectAxisToSlice, True),
            ('Const&rain Motion',
             'Constrain the motion of selected objects to the selected slices',
             self._handlerObjectPlaneLock, True),
            ('Rotate around object axis',
             'Rotate selected objects a specified number of degrees around '
             'their attached axes.', self._handlerObjectAxisRotate,
             True),
            ('---',), # important!  one-element tuple...
            ('Animate Objects',
             'Animate all present objects by controlling exclusive visibility',
             self._handlerObjectAnimation, True),
            ('Invoke Prop Method',
             'Invoke the same method on all the selected objects\'s 3D props',
             self._handlerObjectPropInvokeMethod, True)]

        disableList = self._appendGridCommandsTupleToMenu(
            menu, eventWidget, commandsTuple, disable)
        
        return disableList

    def _attachAxis(self, sObject, twoPoints):
        """Associate the axis defined by the two world points with the
        given tdObject.
        """

        # before we attach this axis, we have to disable the current motion
        # temporarily (if any) else the transform will go bonkers
        motionSwitched = False
        if self.getObjectMotion(sObject):
            self._setObjectMotion(sObject, False)
            motionSwitched = True

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
        # 100 times thinner than it is long
        tubeFilter.SetRadius(d / 100.0)
        tubeFilter.SetInput(lineSource.GetOutput())

        lineMapper = vtk.vtkPolyDataMapper()
        lineMapper.SetInput(tubeFilter.GetOutput())

        lineActor = vtk.vtkActor()
        lineActor.GetProperty().SetColor(1.0, 0.0, 0.0)
        lineActor.SetMapper(lineMapper)

        self.slice3dVWR._threedRenderer.AddActor(lineActor)

        self._tdObjectsDict[sObject]['axisPoints'] = twoPoints
        self._tdObjectsDict[sObject]['axisLineActor'] = lineActor

        if motionSwitched:
            self._setObjectMotion(sObject, True)

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

        # bvm indicates the orientation of the objectAxis w.r.t. the
        # intersection line
        # draw the figures, experiment with what this code does when the
        # lineVector is exactly the same but with opposite direction :)
        if bvm < 0:
            rotAngle *= -1.0

        # 4. create a homogenous transform with this translation and
        #    rotation
        
        newTransform = vtk.vtkTransform()
        newTransform.Identity()
        newTransform.PreMultiply()
        newTransform.Translate(od) # vd was the vertical translation
        tp0n = [-e for e in axisPoints[0]]
        newTransform.Translate(axisPoints[0])
        newTransform.RotateWXYZ(
            rotAngle, rotAxis[0], rotAxis[1], rotAxis[2])
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

        # perform the actual transform and flatten all afterwards
        self._transformObjectProps(tdObject, newTransform)

        # perform other post object motion synchronisation, such as
        # for contours e.g.
        self._postObjectMotionSync(tdObject)

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

        # transform the object and all its thingies
        self._transformObjectProps(tdObject, newTransform)

        # perform other post object motion synchronisation, such as
        # for contours e.g.
        self._postObjectMotionSync(tdObject)

        if motionSwitched:
            self._setObjectMotion(tdObject, True)

    def _bindEvents(self):
        #controlFrame = self.slice3dVWR.controlFrame

        wx.grid.EVT_GRID_CELL_RIGHT_CLICK(
            self._grid, self._handlerGridRightClick)
        wx.grid.EVT_GRID_LABEL_RIGHT_CLICK(
            self._grid, self._handlerGridRightClick)

        wx.grid.EVT_GRID_RANGE_SELECT(
            self._grid, self._handlerGridRangeSelect)
        
        


    def _detachAxis(self, tdObject):
        """Remove any object axis-related metadata and actors if tdObject
        has them.
        """

        try:
            actor = self._tdObjectsDict[tdObject]['axisLineActor']
            self.slice3dVWR._threedRenderer.RemoveActor(actor)
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
        

    def findObjectByName(self, objectName):
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
            raise KeyError
        

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

    def _handlerGridRightClick(self, gridEvent):
        """This will popup a context menu when the user right-clicks on the
        grid.
        """

        pmenu = wx.Menu('Objects Context Menu')

        self._appendGridCommandsToMenu(pmenu, self._grid)
        self._grid.PopupMenu(pmenu, gridEvent.GetPosition())

    def _handlerObjectAnimation(self, event):
        self.slice3dVWR.objectAnimationFrame.Show()
        self.slice3dVWR.objectAnimationFrame.Raise()
        self._objectAnimationReset()

    def _handlerObjectAnimationReset(self, event):
        self._objectAnimationReset()
        
    def _handlerObjectAnimationSlider(self, event):
        frameSlider = self.slice3dVWR.objectAnimationFrame.frameSlider
        self._objectAnimationSetFrame(frameSlider.GetValue())

    def _handlerObjectPropInvokeMethod(self, event):
        methodName = wx.GetTextFromUser(
            'Enter the name of the method that you would like\n'
            'to invoke on all selected objects.')
        if methodName:
            objs = self._getSelectedObjects()            
            try:
                for obj in objs:
                    t = self._tdObjectsDict[obj]['type']
                    prop = None
                    if t == 'vtkPolyData':
                        prop = self._tdObjectsDict[obj]['vtkActor']
                    elif t == 'vtkVolume':
                        prop = obj # this is the vtkVolume
                    else:
                        prop = None

                    if prop:
                        exec('prop.%s' % (methodName,))
                        
            except Exception:
                self._moduleManager.log_error_with_exception(
                    'Could not execute %s on object %s\'s prop.' % \
                    (methodName,
                     self._tdObjectsDict[obj]['objectName']))
                

    def _handlerObjectSelectAll(self, event):
        for row in range(self._grid.GetNumberRows()):
            self._grid.SelectRow(row, True)

    def _handlerObjectDeselectAll(self, event):
        self._grid.ClearSelection()

    def _handlerObjectContourOn(self, event):
        objs = self._getSelectedObjects()
        for obj in objs:
            self._setObjectContouring(obj, True)

        if objs:
            self.slice3dVWR.render3D()

    def _handlerObjectContourOff(self, event):
        objs = self._getSelectedObjects()
        for obj in objs:
            self._setObjectContouring(obj, False)

        if objs:
            self.slice3dVWR.render3D()


    def _handlerObjectSetColour(self, event):
        objs = self._getSelectedObjects()
        
        if objs:
            self.slice3dVWR.setColourDialogColour(
                self._tdObjectsDict[objs[0]]['colour'])
                
            dColour = self.slice3dVWR.getColourDialogColour()
            if dColour:
                for obj in objs:
                    self._setObjectColour(obj, dColour)

        if objs:
            self.slice3dVWR.render3D()

    def _handlerObjectSetOpacity(self, event):


        opacityText = wx.GetTextFromUser(
            'Enter a new opacity value (0.0 to 1.0) for all selected '
            'objects.')

        if opacityText:
            try:
                opacity = float(opacityText)
            except ValueError:
                pass
            else:
                if opacity > 1.0:
                    opacity = 1.0
                elif opacity < 0.0:
                    opacity = 0.0

                objs = self._getSelectedObjects()                    
                for obj in objs:
                    prop = self.findPropByObject(obj)
                    if prop:
                        try:
                            prop.GetProperty().SetOpacity(opacity)
                        except AttributeError:
                            # it could be a volume or somesuch...
                            pass

                if objs:
                    self.slice3dVWR.render3D()
                    
    def _handlerObjectHide(self, event):
        objs = self._getSelectedObjects()

        for obj in objs:
            self._setObjectVisibility(obj, False)

        if objs:
            self.slice3dVWR.render3D()

    def _handlerObjectShow(self, event):
        objs = self._getSelectedObjects()

        for obj in objs:
            self._setObjectVisibility(obj, True)

        if objs:
            self.slice3dVWR.render3D()

    def _handlerObjectScalarVisibilityOn(self, event):
        objs = self._getSelectedObjects()

        for obj in objs:
            self._setObjectScalarVisibility(obj, True)

        if objs:
            self.slice3dVWR.render3D()
        

    def _handlerObjectScalarVisibilityOff(self, event):
        objs = self._getSelectedObjects()

        for obj in objs:
            self._setObjectScalarVisibility(obj, False)

        if objs:
            self.slice3dVWR.render3D()


    def _handlerObjectMotionOff(self, event):
        objs = self._getSelectedObjects()

        for obj in objs:
            self._setObjectMotion(obj, False)

        if objs:
            self.slice3dVWR.render3D()

    def _handlerObjectMotionOn(self, event):
        objs = self._getSelectedObjects()

        for obj in objs:
            self._setObjectMotion(obj, True)

        if objs:
            self.slice3dVWR.render3D()

    def _handlerObjectAttachAxis(self, event):
        """The user should have selected at least two points and an object.
        This will record the axis formed by the two selected points as the
        object axis.  If no points are selected, and an axis already exists,
        we detach the axis.
        """

        worldPoints = self.slice3dVWR.selectedPoints.getSelectedWorldPoints()
        sObjects = self._getSelectedObjects()
        if len(worldPoints) >= 2 and sObjects:
            for sObject in sObjects:
                canChange = True
                if 'axisPoints' in self._tdObjectsDict[sObject]:
                    oName = self._tdObjectsDict[sObject]['objectName']
                    md = wx.MessageDialog(
                        self.slice3dVWR.controlFrame,
                        "Are you sure you want to CHANGE the axis on object "
                        "%s?" % (oName,),
                        "Confirm axis change",
                        wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
                    
                    if md.ShowModal() != wx.ID_YES:
                        canChange = False

                if canChange:
                    # detach any previous stuff
                    self._detachAxis(sObject)
                    # the user asked for it, so we're doing all of 'em
                    self._attachAxis(sObject, worldPoints[0:2])

            # closes for sObject in sObjects...
            if sObjects:
                self.slice3dVWR.render3D()
                
        elif not worldPoints and sObjects:
            # this means the user might want to remove all axes from
            # the sObjects
            md = wx.MessageDialog(
                self.slice3dVWR.controlFrame,
                "Are you sure you want to REMOVE axes "
                "from all selected objects?",
                "Confirm axis removal",
                wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
            if md.ShowModal() == wx.ID_YES:
                for sObject in sObjects:
                    self._detachAxis(sObject)

                if sObjects:
                    self.slice3dVWR.render3D()

        else:
            md = wx.MessageDialog(
                self.slice3dVWR.controlFrame,
                "To attach an axis to an object, you need to select two "
                "points and an object.",
                "Information",
                wx.OK | wx.ICON_INFORMATION)
            md.ShowModal()

    def _handlerObjectAxisToSlice(self, event):
        #
        sObjects = self._getSelectedObjects()
        print len(sObjects)
        sSliceDirections = self.slice3dVWR.sliceDirections.\
                           getSelectedSliceDirections()

        if not sSliceDirections:
            md = wx.MessageDialog(self.slice3dVWR.controlFrame,
                                  "Select at least one slice before "
                                  "using AxisToSlice.",
                                  "Information",
                                  wx.OK | wx.ICON_INFORMATION)
            md.ShowModal()
            return

        if not sObjects:
            md = wx.MessageDialog(self.slice3dVWR.controlFrame,
                                  "Select at least one object before "
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
                    md = wx.MessageDialog(self.slice3dVWR.controlFrame,
                                          "The slices you have selected "
                                          "contain no data.",
                                          "Information",
                                          wx.OK | wx.ICON_INFORMATION)
                    md.ShowModal()
                    return

                try:
                    lineOrigin, lineVector = misc.planePlaneIntersection(
                        pn0, po0, pn1, po1)
                except ValueError, msg:
                    md = wx.MessageDialog(self.slice3dVWR.controlFrame,
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
                md = wx.MessageDialog(self.slice3dVWR.controlFrame,
                                      "You have selected more than two "
                                      "slices. "
                                      "I am not sure what I should think "
                                      "about this.",
                                      "Information",
                                      wx.OK | wx.ICON_INFORMATION)
                md.ShowModal()
                return
        
        if sObjects:
            self.slice3dVWR.render3D()

    def _handlerObjectPlaneLock(self, event):
        """Lock the selected objects to the selected planes.  This will
        constrain future motion to the planes as they are currently defined.
        If no planes are selected, the system will lift the locking.
        """

        sObjects = self._getSelectedObjects()
        sSliceDirections = self.slice3dVWR.sliceDirections.\
                           getSelectedSliceDirections()

        if sObjects and sSliceDirections:
            for sObject in sObjects:
                # first unlock from any previous locks
                self._unlockObjectFromPlanes(sObject)
                for sliceDirection in sSliceDirections:
                    self._lockObjectToPlane(sObject, sliceDirection)

        elif sObjects:
            md = wx.MessageDialog(
                self.slice3dVWR.controlFrame,
                "Are you sure you want to UNLOCK the selected objects "
                "from all slices?",
                "Confirm Object Unlock",
                wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
            
            if md.ShowModal() == wx.ID_YES:
                for sObject in sObjects:
                    self._unlockObjectFromPlanes(sObject)

        else:
            md = wx.MessageDialog(
                self.slice3dVWR.controlFrame,
                "To lock an object to plane, you have to select at least "
                "one object and one slice.",
                "Information",
                wx.OK | wx.ICON_INFORMATION)
            
            md.ShowModal()

    def _handlerObjectAxisRotate(self, event):
        #
        sObjects = self._getSelectedObjects()

        if not sObjects:
            md = wx.MessageDialog(self.slice3dVWR.controlFrame,
                                  "Select at least one object before "
                                  "using rotate around axis.",
                                  "Information",
                                  wx.OK | wx.ICON_INFORMATION)
            md.ShowModal()
            return

        for sObject in sObjects:
            objectDict = self._tdObjectsDict[sObject]
            if 'axisPoints' not in objectDict:
                md = wx.MessageDialog(self.slice3dVWR.controlFrame,
                                      "Object %s has no attached axis "
                                      "around which it can be rotated. "
                                      "Please attach an axis." \
                                      % (objectDict['objectName'],),
                                      "Information",
                                      wx.OK | wx.ICON_INFORMATION)
                md.ShowModal()
                return

            else:
            
                # we have to check for an axis first
                angleText = wx.GetTextFromUser(
                    'Enter the number of degrees to rotate the selected '
                    'objects around their attached axes.')

                if angleText:
                    try:
                        angle = float(angleText)
                    except ValueError:
                        pass
                    else:
                        # first switch of the motion widget (else things
                        # get really confusing)
                        motionSwitched = False
                        if self.getObjectMotion(sObject):
                            self._setObjectMotion(sObject, False)
                            motionSwitched = True

                        # the stored axis points represent the ORIGINAL
                        # location of the axis defining points...
                        # we have to transform these with the current
                        # transform of the axisactor
                        axisMatrix = vtk.vtkMatrix4x4()
                        axisLineActor = objectDict['axisLineActor']
                        axisLineActor.GetMatrix(axisMatrix)
                        axisPoints = objectDict['axisPoints']
                        
                        twoPoints = []
                        twoPoints.append(axisMatrix.MultiplyPoint(
                            axisPoints[0] + (1,))[0:3])
                        twoPoints.append(axisMatrix.MultiplyPoint(
                            axisPoints[1] + (1,))[0:3])
                            

                        # do the actual rotation
                        # calculate the axis vector
                        v = map(operator.sub, twoPoints[1], twoPoints[0])
                        vtk.vtkMath.Normalize(v)
                        # create a transform with the requested rotation
                        newTransform = vtk.vtkTransform()
                        newTransform.Identity()
                        # here we choose PostMultiply, i.e. A * M where M
                        # is the current trfm and A is new so that our
                        # actions have a natural order: Ta * R * To * O
                        # where To is the translation back to the origin,
                        # R is the rotation and Ta is the translation back
                        # to where we started.  O is the object that is being
                        # transformed
                        newTransform.PostMultiply()
                        # we have a vector from 0 to 1, so we have
                        # to translate to 0 first
                        newTransform.Translate([-e for e in twoPoints[0]])
                        # do the rotation
                        newTransform.RotateWXYZ(angle, v)
                        # then transform it back to point 0
                        newTransform.Translate(twoPoints[0])
                        # finally apply the transform
                        self._transformObjectProps(sObject, newTransform)
                        
                        # make sure everything dependent on this tdObject
                        # is updated
                        self._postObjectMotionSync(sObject)

                        # switch motion back on if it was switched off
                        if motionSwitched:
                            self._setObjectMotion(sObject, True)
            
        
        if sObjects:
            self.slice3dVWR.render3D()
            

    def _initialiseGrid(self):
        """Setup the object listCtrl from scratch, mmmkay?
        """

        # setup default selection background
        gsb = self.slice3dVWR.gridSelectionBackground
        self._grid.SetSelectionBackground(gsb)

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

    def _objectAnimationReset(self):
        objectsPerFrameSpinCtrl = self.slice3dVWR.objectAnimationFrame.\
                                  objectsPerFrameSpinCtrl
        objectsPerFrame = objectsPerFrameSpinCtrl.GetValue()
        
        if objectsPerFrame > 0:
            frameSlider = self.slice3dVWR.objectAnimationFrame.frameSlider
            # first tell slider what it can do
            selectedObjects = self._getSelectedObjects()
            numObjects = len(selectedObjects)
            frames = numObjects / objectsPerFrame
            frameSlider.SetRange(0, frames - 1)
            frameSlider.SetValue(0)

            self._objectAnimationSetFrame(0)

    def _objectAnimationSetFrame(self, frame):
        selectedObjects = self._getSelectedObjects()
        numObjects = len(selectedObjects)
        objectsPerFrameSpinCtrl = self.slice3dVWR.objectAnimationFrame.\
                                  objectsPerFrameSpinCtrl
        objectsPerFrame = objectsPerFrameSpinCtrl.GetValue()

        if objectsPerFrame > 0 and \
               frame < numObjects / objectsPerFrame:

            objectNames = []
            selectedRows = self._grid.GetSelectedRows()
            for i in range(objectsPerFrame):
                objectNames.append(self._grid.GetCellValue(
                    selectedRows[frame * objectsPerFrame + i],
                    self._gridNameCol))
                                   
            self._setExclusiveObjectVisibility(objectNames, True)
            self.slice3dVWR.render3D()
        
        

    def _observerMotionBoxWidgetEndInteraction(self, eventObject, eventType):
        # make sure the transform is up to date
        self._observerMotionBoxWidgetInteraction(eventObject, eventType)

        tdObject = self.findObjectByProp(eventObject.GetProp3D())
        self._postObjectMotionSync(tdObject)
        

    def _observerMotionBoxWidgetInteraction(self, eventObject, eventType):
        bwTransform = vtk.vtkTransform()
        eventObject.GetTransform(bwTransform)
        
        eventObject.GetProp3D().SetUserTransform(bwTransform)

        # now make sure that the object axis (if any) is also aligned
        # find the tdObject corresponding to the prop
        tdObject = self.findObjectByProp(eventObject.GetProp3D())
        try:
            # if there's a line, move it too!
            axisLineActor = self._tdObjectsDict[tdObject]['axisLineActor']
            axisLineActor.SetUserTransform(bwTransform)
        except KeyError:
            pass
        

    def _postObjectMotionSync(self, tdObject):
        """Perform any post object motion synchronisation, such as
        recalculating the contours.  This method is called when the user
        has stopped interacting with an object or if the system has
        explicitly moved an object.
        """
        # and update the contours after we're done moving things around
        self.slice3dVWR.sliceDirections.syncContoursToObject(tdObject)

    def removeObject(self, tdObject):
        if not self._tdObjectsDict.has_key(tdObject):
            raise Exception, 'Attempt to remove non-existent tdObject'

        # this will take care of motion boxes and the like
        self._setObjectMotion(tdObject, False)

        oType = self._tdObjectsDict[tdObject]['type']
        if oType == 'vtkVolume':
            self.slice3dVWR._threedRenderer.RemoveVolume(tdObject)
            self.slice3dVWR.render3D()

        elif oType == 'vtkPolyData':
            # remove all contours due to this object
            self._setObjectContouring(tdObject, False)
            
            actor = self._tdObjectsDict[tdObject]['vtkActor']
            self.slice3dVWR._threedRenderer.RemoveActor(actor)

            try:
                # if there was a axisLineActor, remove that as well
                lineActor = self._tdObjectsDict[tdObject]['axisLineActor']
                self.slice3dVWR._threedRenderer.RemoveActor(lineActor)
            except KeyError:
                pass
            
            self.slice3dVWR.render3D()
            
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

    def _setObjectScalarVisibility(self, tdObject, scalarVisibility):
        if self._tdObjectsDict.has_key(tdObject):
            objectDict = self._tdObjectsDict[tdObject]

            
            # in the scene
            if objectDict['type'] == 'vtkPolyData':
                objectDict['vtkActor'].GetMapper().SetScalarVisibility(
                    scalarVisibility)

            else:
                # in these cases, scalarVisibility is NA, so it remains off
                scalarVisibility = False
                pass

            # in our own dict
            objectDict['scalarVisibility'] = bool(scalarVisibility)
            
            # finally in the grid
            gridRow = self.findGridRowByName(objectDict['objectName'])
            if gridRow >= 0:
                genUtils.setGridCellYesNo(
                    self._grid,gridRow, self._gridScalarVisibilityCol,
                    scalarVisibility)
        

    def _setExclusiveObjectVisibility(self, objectNames, visible):
        """Sets the visibility of tdObject to visible and all the other
        objects to the opposite.  Used by animation.
        """

        objs = self._getSelectedObjects()
        for obj in objs:
            objDict = self._tdObjectsDict[obj]
            if objDict['objectName'] in objectNames:
                self._setObjectVisibility(obj, visible)
            else:
                self._setObjectVisibility(obj, not visible)

    def _setObjectContouring(self, tdObject, contour):
        if self._tdObjectsDict.has_key(tdObject):
            objectDict = self._tdObjectsDict[tdObject]
            
            # in our own dict
            objectDict['contour'] = bool(contour)

            if objectDict['type'] == 'vtkPolyData':
                # in the scene
                if contour:
                    self.slice3dVWR.sliceDirections.addContourObject(
                        tdObject, objectDict['vtkActor'])
                else:
                    self.slice3dVWR.sliceDirections.removeContourObject(
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

            # setup our frikking motionBoxWidget, mmmkay?
            if motion:
                if 'motionBoxWidget' in objectDict and \
                   objectDict['motionBoxWidget']:
                    # take care of the old one
                    objectDict['motionBoxWidget'].Off()
                    objectDict['motionBoxWidget'].SetInteractor(None)
                    objectDict['motionBoxWidget'] = None

                # we like to do it anew
                objectDict['motionBoxWidget'] = vtkdevide.\
                                                vtkBoxWidgetConstrained()
                bw = objectDict['motionBoxWidget']
                    
                # let's switch on scaling for now... (I used to have this off,
                # but I can't remember exactly why)
                bw.ScalingEnabledOn()
                # the balls only confuse us!
                bw.HandlesOff()
                # without the balls, the outlines aren't needed either
                bw.OutlineCursorWiresOff()
                bw.SetInteractor(self.slice3dVWR.threedFrame.threedRWI)
                # also "flatten" the actor (i.e. integrate its UserTransform)
                misc.flattenProp3D(objectDict['vtkActor'])
                # and the axis, if any
                try:
                    misc.flattenProp3D(objectDict['axisLineActor'])
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
#                     ipw = self.slice3dVWR._sliceDirections[0]._ipws[0]
#                 except:
#                     # no plane, so we don't do anything
#                     pass
#                 else:
#                     bw.ConstrainToPlaneOn()
#                     bw.SetConstrainPlaneNormal(ipw.GetNormal())

                self._setupMotionConstraints(bw, tdObject)
                

            else: # if NOT motion
                if 'motionBoxWidget' in objectDict and \
                   objectDict['motionBoxWidget']:
                    try:
                        # let's flatten the prop again (if there is one)
                        misc.flattenProp3D(objectDict['vtkActor'])
                        # and flatten the axis (if any)
                        misc.flattenProp3D(objectDict['axisLineActor'])
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

    def _transformObjectProps(self, tdObject, transform):
        """This will perform the final transformation on all props belonging
        to an object, including the main prop and all extras, such as the
        optional object axis.  It will also make sure all the transforms of
        all props are flattened.
        """

        try:
            mainProp = self.findPropByObject(tdObject)
            objectDict = self._tdObjectsDict[tdObject]
        except KeyError:
            # invalid tdObject!
            return

        props = [mainProp]

        try:
            props.append(objectDict['axisLineActor'])
        except KeyError:
            # no problem
            pass

        for prop in props:
            # first we make sure that there's no UserTransform
            misc.flattenProp3D(prop)
            # then set the UserTransform that we want
            prop.SetUserTransform(transform)
            # then flatten the f*cker (i.e. UserTransform absorbed)
            misc.flattenProp3D(prop)

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
