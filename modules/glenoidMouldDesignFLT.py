# glenoidMouldDesigner.py copyright 2003 Charl P. Botha http://cpbotha.net/
# $Id: glenoidMouldDesignFLT.py,v 1.4 2003/03/20 16:48:03 cpbotha Exp $
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
            angleIncr = 2.0 * vtk.vtkMath.Pi() / 8.056
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

                cut = vtk.vtkCutter()
                cut.SetInput(self._inputPolyData)
                cut.SetCutFunction(plane)
                cut.GenerateCutScalarsOn()
                cut.SetValue(0,1)
                cut.Update()

                contour = cut.GetOutput()

                # now find line segment closest to self._giaProximal
                pl = vtk.vtkPointLocator()
                pl.SetDataSet(contour)
                pl.BuildLocator()
                startPtId = pl.FindClosestPoint(self._giaProximal)

                # we need to find out which cells belong to which points
                contour.BuildLinks()
                
                cellIds = vtk.vtkIdList()
                contour.GetPointCells(startPtId, cellIds)


                twoLineIds = cellIds.GetId(0), cellIds.GetId(1)

                ptIds = vtk.vtkIdList()
                cellIds = vtk.vtkIdList()
                newCellArray = vtk.vtkCellArray()
                
                for startLineId in twoLineIds:

                    # we have a startLineId, a startPtId and polyData
                    curStartPtId = startPtId
                    curLineId = startLineId
                    

                    for i in range(50):
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

                        # stop criterion here, if not, then store
                        print "inserting %d\n" % (curLineId,)
                        newCellArray.InsertNextCell(contour.GetCell(curLineId))


                        # get ready for next iteration
                        curStartPtId = nextPointId
                        curLineId = nextLineId
                

                newPolyData = vtk.vtkPolyData()
                newPolyData.SetLines(newCellArray)
                newPolyData.SetPoints(contour.GetPoints())
                #tf = vtk.vtkRibbonFilter()
                #tf.SetInput(contour)
                #tf.Update()

                stuff.append(newPolyData)


            ap = vtk.vtkAppendPolyData()
            # copy everything to output (for testing)
            for thing in stuff[:1]:
                ap.AddInput(thing)

            ap.Update()
            self._outputPolyData.DeepCopy(ap.GetOutput())

    def view(self):
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()

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
