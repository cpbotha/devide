# glenoidMouldDesigner.py copyright 2003 Charl P. Botha http://cpbotha.net/
# $Id: glenoidMouldDesignFLT.py,v 1.8 2003/03/22 00:56:59 cpbotha Exp $
# dscas3 module that designs glenoid moulds by making use of insertion
# axis and model of scapula

# this module doesn't satisfy the event handling requirements of DSCAS3 yet
# if you call update on the output PolyData, this module won't know to
# execute, because at the moment main processing takes place in Python-land
# this will be so at least until we convert the processing to a vtkSource
# child that has the PolyData as output or until we fake it with Observers
# This is not critical.

from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import operator
import vtk
from wxPython.wx import *

class glenoidMouldDesignFLT(moduleBase, noConfigModuleMixin):

    def __init__(self, moduleManager):
        
        # call parent constructor
        moduleBase.__init__(self, moduleManager)
        # and mixin
        noConfigModuleMixin.__init__(self)

        self._inputPolyData = None
        self._inputPoints = None
        self._inputPointsOID = None
        self._giaProximal = None
        self._giaDistal = None
        self._outputPolyData = vtk.vtkPolyData()

        # create the frame and display it proudly!
        self._createViewFrame('Glenoid Mould Designer View',
                              {'Output Polydata': self._outputPolyData})
        self._viewFrame.Show(True)

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
        if self._giaDistal and self._giaProximal and self._inputPolyData:
            # construct eight planes with the insertion axis as mid-line
            # the planes should go somewhat further proximally than the
            # proximal insertion axis point

            # first calculate the distal-proximal glenoid insertion axis
            gia = tuple(map(operator.sub, self._giaProximal, self._giaDistal))
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
                
                origin = map(operator.add, self._giaDistal, y)
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

                # now find line segment closest to self._giaProximal
                pl = vtk.vtkPointLocator()
                pl.SetDataSet(contour)
                pl.BuildLocator()
                startPtId = pl.FindClosestPoint(self._giaProximal)

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
                    while onGlenoid:
                        contour.GetCellPoints(curLineId, ptIds)
                        ptId0 = ptIds.GetId(0)
                        ptId1 = ptIds.GetId(1)
                        nextPointId = [ptId0, ptId1]\
                                      [bool(ptId0 == curStartPtId)]

                        contour.GetPointCells(nextPointId, cellIds)
                        cId0 = cellIds.GetId(0)
                        cId1 = cellIds.GetId(1)
                        nextLineId = [cId0, cId1]\
                                     [bool(cId0 == curLineId)]


                        # get the normal for the current point
                        n = contour.GetPointData().GetNormals().GetTuple3(
                            curStartPtId)

                        # get the current point
                        pt0 = contour.GetPoints().GetPoint(curStartPtId)

                        # stop criterion here
                        if abs(vtk.vtkMath.Dot(giaN, n)) > 0.8:
                            # store the real ptid, point coords and normal
                            lines[lineIdx].append((curStartPtId,
                                               tuple(pt0), tuple(n)))
                            
                            # get ready for next iteration
                            curStartPtId = nextPointId
                            curLineId = nextLineId
                            
                        else:
                            onGlenoid = False
                
                    # closes: for i in range(20)
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
                    for vertexIdx in range(len(house)):
                        ptId = newPoints.InsertNextPoint(house[vertexIdx])
                        idLists[vertexIdx].InsertNextId(ptId)
                    
                # create a cell with the 5 lines
                newCellArray = vtk.vtkCellArray()
                for idList in idLists:
                    newCellArray.InsertNextCell(idList)
                #newCellArray.InsertNextCell(idLists[0])

                newPolyData = vtk.vtkPolyData()
                newPolyData.SetLines(newCellArray)
                newPolyData.SetPoints(newPoints)

                rsf = vtk.vtkRuledSurfaceFilter()
                rsf.CloseSurfaceOn()
                rsf.SetRuledModeToPointWalk()
                rsf.SetInput(newPolyData)
                rsf.Update()

                stuff.append(rsf.GetOutput())
                #stuff.append(cut.GetOutput())
                stuff.append(ps.GetOutput())

            
            # closes: for i in range(4)
            
            ap = vtk.vtkAppendPolyData()
            # copy everything to output (for testing)
            for thing in stuff:
                ap.AddInput(thing)

            ap.Update()
            self._outputPolyData.DeepCopy(ap.GetOutput())

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
        Python tuples.
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

        return (tuple(startPoint), p1, p2, p3, p4)

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
        
        for point in edgeLine:
            housePoints = self._buildHouse(point[1], point[2], cutPlane)
            # check here to see if negative volume occurs
            newEdgeLine.append(housePoints)

        return newEdgeLine
            
            

    def _inputPointsObserver(self, obj):
        # extract a list from the input points
        if self._inputPoints:
            # extract the two points with labels 'GIA Proximal'
            # and 'GIA Distal'
            
            giaProximal = [i['world'] for i in self._inputPoints if i['name'] == 'GIA Proximal']

            giaDistal = [i['world'] for i in self._inputPoints if i['name'] == 'GIA Distal']

            if giaProximal and giaDistal:
                # we only apply these points to our internal parameters
                # if they're valid and if they're new
                self._giaProximal = giaProximal[0]
                self._giaDistal = giaDistal[0]
