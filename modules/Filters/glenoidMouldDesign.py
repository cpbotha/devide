# glenoidMouldDesigner.py copyright 2003 Charl P. Botha http://cpbotha.net/
# $Id: glenoidMouldDesign.py,v 1.3 2004/01/15 10:46:27 cpbotha Exp $
# devide module that designs glenoid moulds by making use of insertion
# axis and model of scapula

# this module doesn't satisfy the event handling requirements of DeVIDE yet
# if you call update on the output PolyData, this module won't know to
# execute, because at the moment main processing takes place in Python-land
# this will be so at least until we convert the processing to a vtkSource
# child that has the PolyData as output or until we fake it with Observers
# This is not critical.

import math
from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import operator
import vtk
from wxPython.wx import *

class glenoidMouldDesign(moduleBase, noConfigModuleMixin):

    drillGuideInnerDiameter = 3
    drillGuideOuterDiameter = 5
    drillGuideHeight = 10

    def __init__(self, moduleManager):
        
        # call parent constructor
        moduleBase.__init__(self, moduleManager)
        # and mixin
        noConfigModuleMixin.__init__(self)

        self._inputPolyData = None
        self._inputPoints = None
        self._inputPointsOID = None
        self._giaGlenoid = None
        self._giaHumerus = None
        self._glenoidEdge = None
        self._outputPolyData = vtk.vtkPolyData()

        # create the frame and display it proudly!
        self._viewFrame = self._createViewFrame(
            {'Output Polydata': self._outputPolyData})

    def close(self):
        # disconnect all inputs
        self.setInput(0, None)
        self.setInput(1, None)
        # take care of critical instances
        self._outputPolyData = None
        # mixin close
        noConfigModuleMixin.close(self)

    def getInputDescriptions(self):
        return('Scapula vtkPolyData', 'Insertion axis (points)')

    def setInput(self, idx, inputStream):
        if idx == 0:
            # will work for None and not-None
            self._inputPolyData = inputStream
        else:
            if inputStream is not self._inputPoints:
                if self._inputPoints:
                    self._inputPoints.removeObserver(self._inputPointsOID)

                if inputStream:
                    self._inputPointsOID = inputStream.addObserver(
                        self._inputPointsObserver)

                self._inputPoints = inputStream

                # initial update
                self._inputPointsObserver(None)
                    

    def getOutputDescriptions(self):
        return ('Mould design (vtkPolyData)',) # for now

    def getOutput(self, idx):
        return self._outputPolyData

    def logicToConfig(self):
        pass

    def configToLogic(self):
        pass

    def viewToConfig(self):
        pass

    def configToView(self):
        pass

    def executeModule(self):
        if self._giaHumerus and self._giaGlenoid and \
           len(self._glenoidEdge) >= 6 and self._inputPolyData:

            # _glenoidEdgeImplicitFunction
            
            # construct eight planes with the insertion axis as mid-line
            # the planes should go somewhat further proximally than the
            # proximal insertion axis point

            # first calculate the distal-proximal glenoid insertion axis
            gia = tuple(map(operator.sub, self._giaGlenoid, self._giaHumerus))
            # and in one swift move, we normalize it and get the magnitude
            giaN = list(gia)
            giaM = vtk.vtkMath.Normalize(giaN)

            # extend gia with a few millimetres
            giaM += 5
            gia = tuple([giaM * i  for i in giaN])

            stuff = []
            yN = [0,0,0]
            zN = [0,0,0]
            angleIncr = 2.0 * vtk.vtkMath.Pi() / 8.0
            for i in range(4):
                angle = float(i) * angleIncr
                vtk.vtkMath.Perpendiculars(gia, yN, zN, angle)
                # each ridge is 1 cm (10 mm) - we'll change this later
                y = [10.0 * j for j in yN]
                
                origin = map(operator.add, self._giaHumerus, y)
                point1 = map(operator.add, origin, [-2.0 * k for k in y])
                point2 = map(operator.add, origin, gia)

                # now create the plane source
                ps = vtk.vtkPlaneSource()
                ps.SetOrigin(origin)
                ps.SetPoint1(point1)
                ps.SetPoint2(point2)
                ps.Update()

                plane = vtk.vtkPlane()
                plane.SetOrigin(ps.GetOrigin())
                plane.SetNormal(ps.GetNormal())

                pdn = vtk.vtkPolyDataNormals()
                pdn.SetInput(self._inputPolyData)

                cut = vtk.vtkCutter()
                cut.SetInput(pdn.GetOutput())
                cut.SetCutFunction(plane)
                cut.GenerateCutScalarsOn()
                cut.SetValue(0,0)
                cut.Update()

                contour = cut.GetOutput()

                # now find line segment closest to self._giaGlenoid
                pl = vtk.vtkPointLocator()
                pl.SetDataSet(contour)
                pl.BuildLocator()
                startPtId = pl.FindClosestPoint(self._giaGlenoid)

                cellIds = vtk.vtkIdList()
                contour.GetPointCells(startPtId, cellIds)

                twoLineIds = cellIds.GetId(0), cellIds.GetId(1)

                ptIds = vtk.vtkIdList()
                cellIds = vtk.vtkIdList()

                # we'll use these to store tuples:
                # (ptId, (pt0, pt1, pt2), (n0, n1, n2))
                lines = [[],[]]
                lineIdx = 0
                for startLineId in twoLineIds:

                    # we have a startLineId, a startPtId and polyData
                    curStartPtId = startPtId
                    curLineId = startLineId
                    
                    onGlenoid = True
                    offCount = 0
                    while onGlenoid:
                        contour.GetCellPoints(curLineId, ptIds)
                        if ptIds.GetNumberOfIds() != 2:
                            print 'aaaaaaaaaaaaack!'
                            
                        ptId0 = ptIds.GetId(0)
                        ptId1 = ptIds.GetId(1)
                        nextPointId = [ptId0, ptId1]\
                                      [bool(ptId0 == curStartPtId)]

                        contour.GetPointCells(nextPointId, cellIds)
                        if cellIds.GetNumberOfIds() != 2:
                            print 'aaaaaaaaaaaaaaaack2!'
                        cId0 = cellIds.GetId(0)
                        cId1 = cellIds.GetId(1)
                        nextLineId = [cId0, cId1]\
                                     [bool(cId0 == curLineId)]


                        # get the normal for the current point
                        n = contour.GetPointData().GetNormals().GetTuple3(
                            curStartPtId)

                        # get the current point
                        pt0 = contour.GetPoints().GetPoint(curStartPtId)

                        # store the real ptid, point coords and normal
                        lines[lineIdx].append((curStartPtId,
                                               tuple(pt0), tuple(n)))

                        
                        if vtk.vtkMath.Dot(giaN, n) > -0.9:
                            # this means that this point could be falling off
                            # the glenoid, let's make a note of the incident
                            offCount += 1
                            # if the last N points have been "off" the glenoid,
                            # it could mean we've really fallen off!
                            if offCount >= 40:
                                del lines[lineIdx][-40:]
                                onGlenoid = False

                        # get ready for next iteration
                        curStartPtId = nextPointId
                        curLineId = nextLineId

                
                    # closes: while onGlenoid
                    lineIdx += 1

                # closes: for startLineId in twoLineIds
                # we now have two line lists... we have to combine them and
                # make sure it still constitutes one long line
                lines[0].reverse()
                edgeLine = lines[0] + lines[1]

                # do line extrusion resulting in a list of 5-element tuples,
                # each tuple representing the 5 3-d vertices of a "house"
                houses = self._lineExtrudeHouse(edgeLine, plane)
                
                # we will dump ALL the new points in here
                newPoints = vtk.vtkPoints()
                newPoints.SetDataType(contour.GetPoints().GetDataType())
                # but we're going to create 5 lines
                idLists = [vtk.vtkIdList() for i in range(5)]

                for house in houses:
                    for vertexIdx in range(5):
                        ptId = newPoints.InsertNextPoint(house[vertexIdx])
                        idLists[vertexIdx].InsertNextId(ptId)
                    
                # create a cell with the 5 lines
                newCellArray = vtk.vtkCellArray()
                for idList in idLists:
                    newCellArray.InsertNextCell(idList)

                newPolyData = vtk.vtkPolyData()
                newPolyData.SetLines(newCellArray)
                newPolyData.SetPoints(newPoints)


                rsf = vtk.vtkRuledSurfaceFilter()
                rsf.CloseSurfaceOn()
                #rsf.SetRuledModeToPointWalk()
                rsf.SetRuledModeToResample()
                rsf.SetResolution(128, 4)
                rsf.SetInput(newPolyData)
                rsf.Update()

                stuff.append(rsf.GetOutput())

                # also add two housies to cap all the ends
                capHousePoints = vtk.vtkPoints()
                capHouses = []
                if len(houses) > 1:
                    # we only cap if there are at least two houses
                    capHouses.append(houses[0])
                    capHouses.append(houses[-1])
                    
                capHouseIdLists = [vtk.vtkIdList() for dummy in capHouses]
                for capHouseIdx in range(len(capHouseIdLists)):
                    house = capHouses[capHouseIdx]
                    for vertexIdx in range(5):
                        ptId = capHousePoints.InsertNextPoint(house[vertexIdx])
                        capHouseIdLists[capHouseIdx].InsertNextId(ptId)

                if capHouseIdLists:
                    newPolyArray = vtk.vtkCellArray()
                    for capHouseIdList in capHouseIdLists:
                        newPolyArray.InsertNextCell(capHouseIdList)

                    capPolyData = vtk.vtkPolyData()
                    capPolyData.SetPoints(capHousePoints)
                    capPolyData.SetPolys(newPolyArray)
                        
                    # FIXME: put back
                    stuff.append(capPolyData)
            
            # closes: for i in range(4)
            ap = vtk.vtkAppendPolyData()
            # copy everything to output (for testing)
            for thing in stuff:
                ap.AddInput(thing)
            #ap.AddInput(stuff[0])
 
            # seems to be important for vtkAppendPolyData
            ap.Update()

            # now cut it with the FBZ planes
            fbzSupPlane = self._fbzCutPlane(self._fbzSup, giaN,
                                            self._giaGlenoid)
            fbzSupClip = vtk.vtkClipPolyData()
            fbzSupClip.SetClipFunction(fbzSupPlane)
            fbzSupClip.SetValue(0)
            fbzSupClip.SetInput(ap.GetOutput())

            fbzInfPlane = self._fbzCutPlane(self._fbzInf, giaN,
                                            self._giaGlenoid)
            fbzInfClip = vtk.vtkClipPolyData()
            fbzInfClip.SetClipFunction(fbzInfPlane)
            fbzInfClip.SetValue(0)
            fbzInfClip.SetInput(fbzSupClip.GetOutput())

            cylinder = vtk.vtkCylinder()
            cylinder.SetCenter([0,0,0])
            # we make the cut-cylinder slightly larger... it's only there
            # to cut away the surface edges, so precision is not relevant
            cylinder.SetRadius(self.drillGuideInnerDiameter / 2.0)

            # cylinder is oriented along y-axis (0,1,0) -
            # we need to calculate the angle between the y-axis and the gia
            # 1. calc dot product (|a||b|cos(\phi))
            cylDotGia = - giaN[1]
            # 2. because both factors are normals, angle == acos
            phiRads = math.acos(cylDotGia)
            # 3. cp is the vector around which gia can be turned to
            #    coincide with the y-axis
            cp = [0,0,0]
            vtk.vtkMath.Cross((-giaN[0], -giaN[1], -giaN[2]),
                              (0.0, 1.0, 0.0), cp)

            # this transform will be applied to all points BEFORE they are
            # tested on the cylinder implicit function
            trfm = vtk.vtkTransform()
            # it's premultiply by default, so the last operation will get
            # applied FIRST:
            # THEN rotate it around the cp axis so it's relative to the
            # y-axis instead of the gia-axis
            trfm.RotateWXYZ(phiRads * vtk.vtkMath.RadiansToDegrees(),
                            cp[0], cp[1], cp[2])
            # first translate the point back to the origin
            trfm.Translate(-self._giaGlenoid[0], -self._giaGlenoid[1],
                           -self._giaGlenoid[2])

            cylinder.SetTransform(trfm)

            cylinderClip = vtk.vtkClipPolyData()
            cylinderClip.SetClipFunction(cylinder)
            cylinderClip.SetValue(0)
            cylinderClip.SetInput(fbzInfClip.GetOutput())
            cylinderClip.GenerateClipScalarsOn()

            ap2 = vtk.vtkAppendPolyData()
            ap2.AddInput(cylinderClip.GetOutput())
            # this will cap the just cut polydata
            ap2.AddInput(self._capCutPolyData(fbzSupClip))
            ap2.AddInput(self._capCutPolyData(fbzInfClip))
            # thees one she dosint werk so gooood
            #ap2.AddInput(self._capCutPolyData(cylinderClip))

            # now add outer guide cylinder, NOT capped
            cs1 = vtk.vtkCylinderSource()
            cs1.SetResolution(32)
            cs1.SetRadius(self.drillGuideOuterDiameter / 2.0)
            cs1.CappingOff()
            cs1.SetHeight(self.drillGuideHeight) # 15 mm height
            cs1.SetCenter(0,0,0)
            cs1.Update()

            # inner cylinder
            cs2 = vtk.vtkCylinderSource()
            cs2.SetResolution(32)
            cs2.SetRadius(self.drillGuideInnerDiameter / 2.0)
            cs2.CappingOff()
            cs2.SetHeight(self.drillGuideHeight) # 15 mm height
            cs2.SetCenter(0,0,0)
            cs2.Update()

            # top cap
            tc = vtk.vtkDiskSource()
            tc.SetInnerRadius(self.drillGuideInnerDiameter / 2.0)
            tc.SetOuterRadius(self.drillGuideOuterDiameter / 2.0)
            tc.SetCircumferentialResolution(64)

            tcTrfm = vtk.vtkTransform()

            # THEN flip it so that its centre-line is the y-axis
            tcTrfm.RotateX(90)
            # FIRST translate the disc
            tcTrfm.Translate(0,0,- self.drillGuideHeight / 2.0)            
            tcTPDF = vtk.vtkTransformPolyDataFilter()
            tcTPDF.SetTransform(tcTrfm)
            tcTPDF.SetInput(tc.GetOutput())

            # bottom cap
            bc = vtk.vtkDiskSource()
            bc.SetInnerRadius(self.drillGuideInnerDiameter / 2.0)
            bc.SetOuterRadius(self.drillGuideOuterDiameter / 2.0)
            bc.SetCircumferentialResolution(64)

            bcTrfm = vtk.vtkTransform()

            # THEN flip it so that its centre-line is the y-axis
            bcTrfm.RotateX(90)
            # FIRST translate the disc
            bcTrfm.Translate(0,0, self.drillGuideHeight / 2.0)            
            bcTPDF = vtk.vtkTransformPolyDataFilter()
            bcTPDF.SetTransform(bcTrfm)
            bcTPDF.SetInput(bc.GetOutput())

            tubeAP = vtk.vtkAppendPolyData()
            tubeAP.AddInput(cs1.GetOutput())
            tubeAP.AddInput(cs2.GetOutput())
            tubeAP.AddInput(tcTPDF.GetOutput())
            tubeAP.AddInput(bcTPDF.GetOutput())            

            # we have to transform this fucker as well
            csTrfm = vtk.vtkTransform()
            # go half the height + 2mm upwards from surface
            drillGuideCentre = - 1.0 * self.drillGuideHeight / 2.0 - 2
            cs1Centre = map(operator.add,
                            self._giaGlenoid,
                            [drillGuideCentre * i for i in giaN])
            # once again, this is performed LAST
            csTrfm.Translate(cs1Centre)
            # and this FIRST (we have to rotate the OTHER way than for
            # the implicit cylinder cutting, because the cylinder is
            # transformed from y-axis to gia, not the other way round)
            csTrfm.RotateWXYZ(-phiRads * vtk.vtkMath.RadiansToDegrees(),
                              cp[0], cp[1], cp[2])
            # actually perform the transform
            csTPDF = vtk.vtkTransformPolyDataFilter()
            csTPDF.SetTransform(csTrfm)
            csTPDF.SetInput(tubeAP.GetOutput())
            csTPDF.Update()

            ap2.AddInput(csTPDF.GetOutput())

            ap2.Update()
            
            self._outputPolyData.DeepCopy(ap2.GetOutput())

    def view(self):
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()


    def _buildHouse(self, startPoint, startPointNormal, cutPlane):
        """Calculate the vertices of a single house.

        Given a point on the cutPlane, the normal at that point and
        the cutPlane normal, this method will calculate and return the
        five points (including the start point) defining the
        upside-down house.  The house is of course oriented with the point
        normal projected onto the cutPlane (then normalized again) and the
        cutPlaneNormal.

        
        p3 +--+ p2
           |  |
        p4 +--+ p1
            \/
            p0

        startPoint, startPointNormal and cutPlaneNormal are all 3-element
        Python tuples.  Err, this now returns 6 points.  The 6th is a
        convenience so that our calling function can easily check for
        negative volume.  See _lineExtrudeHouse.
        """


        # xo = x - o
        # t = xo dot normal
        # h = x - t * normal
        t = vtk.vtkMath.Dot(startPointNormal, cutPlane.GetNormal())
        houseNormal = map(operator.sub, startPointNormal,
                          [t * i for i in cutPlane.GetNormal()])
        
        vtk.vtkMath.Normalize(houseNormal)
        
        houseNormal3 = [3.0 * i for i in houseNormal]
        cutPlaneNormal1_5 = [1.5 * i for i in cutPlane.GetNormal()]
        mp = map(operator.add, startPoint, houseNormal3)
        p1 = tuple(map(operator.add, mp, cutPlaneNormal1_5))
        p2 = tuple(map(operator.add, p1, houseNormal3))
        p4 = tuple(map(operator.sub, mp, cutPlaneNormal1_5))
        p3 = tuple(map(operator.add, p4, houseNormal3))
        p5 = tuple(map(operator.add, mp, houseNormal3))

        return (tuple(startPoint), p1, p2, p3, p4, p5)

    def _capCutPolyData(self, clipPolyData):
        # set a vtkCutter up exactly like the vtkClipPolyData
        cutter = vtk.vtkCutter()
        cutter.SetCutFunction(clipPolyData.GetClipFunction())
        cutter.SetInput(clipPolyData.GetInput())
        cutter.SetValue(0, clipPolyData.GetValue())
        cutter.SetGenerateCutScalars(clipPolyData.GetGenerateClipScalars())

        cutStripper = vtk.vtkStripper()
        cutStripper.SetInput(cutter.GetOutput())
        cutStripper.Update()

        cutPolyData = vtk.vtkPolyData()
        cutPolyData.SetPoints(cutStripper.GetOutput().GetPoints())
        cutPolyData.SetPolys(cutStripper.GetOutput().GetLines())

        cpd = vtk.vtkCleanPolyData()
        cpd.SetInput(cutPolyData)

        tf = vtk.vtkTriangleFilter()
        tf.SetInput(cpd.GetOutput())
        tf.Update()
        return tf.GetOutput()


    def _fbzCutPlane(self, fbz, giaN, giaGlenoid):
        """Calculate cut-plane corresponding to fbz.

        fbz is a list containing the two points defining a single FBZ
        (forbidden zone).  giaN is the glenoid-insertion axis normal.
        giaGlenoid is the user-selected gia point on the glenoid.

        This method will return a cut-plane to enforce the given fbz such
        that giaGlenoid is on the inside of the implicit plane.
        """
        
        fbzV = map(operator.sub, fbz[0], fbz[1])
        fbzPN = [0,0,0]
        vtk.vtkMath.Cross(fbzV, giaN, fbzPN)
        vtk.vtkMath.Normalize(fbzPN)
        fbzPlane = vtk.vtkPlane()
        fbzPlane.SetOrigin(fbz[0])
        fbzPlane.SetNormal(fbzPN)
        insideVal = fbzPlane.EvaluateFunction(giaGlenoid)
        if insideVal < 0:
            # eeep, it's outside, so flip the planeNormal
            fbzPN = [-1.0 * i for i in fbzPN]
            fbzPlane.SetNormal(fbzPN)

        return fbzPlane

    def _glenoidEdgeImplicitFunction(self, giaGlenoid, edgePoints):
        """Given the on-glenoid point of the glenoid insertion axis and 6
        points (in sequence) around the glenoid edge, this will construct
        a vtk implicit function that can be used to check whether surface
        points are inside or outside.
        """

        

    def _lineExtrudeHouse(self, edgeLine, cutPlane):
        """Extrude the house (square with triangle as roof) along edgeLine.

        edgeLine is a list of tuples where each tuple is:
        (ptId, (p0, p1, p2), (n0, n1, n2)) with P the point coordinate and
        N the normal at that point.  The normal determines the orientation
        of the housy.

        The result is just a line extrusion, i.e. no surfaces yet.  In order
        to do that, run the output (after it has been converted to a polydata)
        through a vtkRuledSurfaceFilter.

        This method returns a list of 5-element tuples.
        """

        newEdgeLine = []

        prevHousePoint0 = None
        prevHousePoint5 = None
        for point in edgeLine:
            housePoints = self._buildHouse(point[1], point[2], cutPlane)
            if prevHousePoint0:
                v0 = map(operator.sub, housePoints[0], prevHousePoint0)
                v1 = map(operator.sub, housePoints[5], prevHousePoint5)
                # bad-assed trick to test for negative volume
                if vtk.vtkMath.Dot(v0, v1) < 0.0:
                    negativeVolume = 1
                else:
                    negativeVolume = 0

            else:
                negativeVolume = 0

            if not negativeVolume:
                newEdgeLine.append(housePoints[:5])
                # we only store it as previous if we actually add it
                prevHousePoint0 = housePoints[0]
                prevHousePoint5 = housePoints[5]

        return newEdgeLine
            
            

    def _inputPointsObserver(self, obj):
        # extract a list from the input points
        if self._inputPoints:
            # extract the two points with labels 'GIA Glenoid'
            # and 'GIA Humerus'
            
            giaGlenoid = [i['world'] for i in self._inputPoints
                          if i['name'] == 'GIA Glenoid']
            
            giaHumerus = [i['world'] for i in self._inputPoints
                          if i['name'] == 'GIA Humerus']

            glenoidEdge = [i['world'] for i in self._inputPoints
                           if i['name'] == 'Glenoid Edge Point']

            if giaGlenoid and giaHumerus and \
               len(glenoidEdge) >= 6:
                # we only apply these points to our internal parameters
                # if they're valid and if they're new
                self._giaGlenoid = giaGlenoid[0]
                self._giaHumerus = giaHumerus[0]
                self._glenoidEdge = glenoidEdge[:6]
