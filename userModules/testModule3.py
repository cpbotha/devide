# IDEA:
# use vtkPolyDataConnectivityFilter with minima as seed points

from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
from wxPython.wx import *
import vtk

class testModule3(moduleBase, noConfigModuleMixin):

    """Module to prototype modification of homotopy and subsequent
    watershedding of curvature-on-surface image.
    """

    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)
        # initialise any mixins we might have
        noConfigModuleMixin.__init__(self)

        mm = self._moduleManager

        self._cleaner = vtk.vtkCleanPolyData()

        self._tf = vtk.vtkTriangleFilter()
        self._tf.SetInput(self._cleaner.GetOutput())
        
        self._wspdf = vtk.vtkWindowedSincPolyDataFilter()
        #self._wspdf.SetNumberOfIterations(50)
        self._wspdf.SetInput(self._tf.GetOutput())
        self._wspdf.SetProgressText('smoothing')
        self._wspdf.SetProgressMethod(lambda s=self, mm=mm:
                                      mm.vtk_progress_cb(s._wspdf))

        self._cleaner2 = vtk.vtkCleanPolyData()
        self._cleaner2.SetInput(self._tf.GetOutput())

        self._curvatures = vtk.vtkCurvatures()
        self._curvatures.SetCurvatureTypeToMean()        
        self._curvatures.SetInput(self._cleaner2.GetOutput())


        self._tf.SetProgressText('triangulating')
        self._tf.SetProgressMethod(lambda s=self, mm=mm:
                                   mm.vtk_progress_cb(s._tf))

        self._curvatures.SetProgressText('calculating curvatures')
        self._curvatures.SetProgressMethod(lambda s=self, mm=mm:
                                           mm.vtk_progress_cb(s._curvatures))

        self._inputPoints = None
        self._inputPointsOID = None
        self._giaGlenoid = None
        self._outsidePoints = None
        self._outputPolyDataARB = vtk.vtkPolyData()
        self._outputPolyDataHM = vtk.vtkPolyData()

        self._createViewFrame('Test Module View',
                              {'vtkTriangleFilter' : self._tf,
                               'vtkCurvatures' : self._curvatures})

        self._viewFrame.Show(True)

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)
        # don't forget to call the close() method of the vtkPipeline mixin
        noConfigModuleMixin.close(self)
        # get rid of our reference
        del self._cleaner
        del self._cleaner2
        del self._wspdf
        del self._curvatures
        del self._tf

        del self._inputPoints
        del self._outputPolyDataARB
        del self._outputPolyDataHM

    def getInputDescriptions(self):
	return ('vtkPolyData', 'Watershed minima')

    def setInput(self, idx, inputStream):
        if idx == 0:
            self._cleaner.SetInput(inputStream)
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
        return ('ARB PolyData output', 'Homotopically modified polydata')

    def getOutput(self, idx):
        if idx == 0:
            return self._outputPolyDataARB
        else:
            return self._outputPolyDataHM

    def logicToConfig(self):
        pass

    def configToLogic(self):
        pass

    def viewToConfig(self):
        pass

    def configToView(self):
        pass
    

    def executeModule(self):
        if self._cleaner.GetInput() and \
               self._outsidePoints and self._giaGlenoid:
            
            self._curvatures.Update()
            # vtkCurvatures has added a mean curvature array to the
            # pointData of the output polydata

            pd = self._curvatures.GetOutput()

            # make a deep copy of the data that we can work with
            tempPd1 = vtk.vtkPolyData()
            tempPd1.DeepCopy(self._curvatures.GetOutput())

            # and now we have to unsign it!
            tempPd1Scalars = tempPd1.GetPointData().GetScalars()
            for i in xrange(tempPd1Scalars.GetNumberOfTuples()):
                a = tempPd1Scalars.GetTuple1(i)
                tempPd1Scalars.SetTuple1(i, float(abs(a)))

            self._outputPolyDataARB.DeepCopy(tempPd1)

            # BUILDING NEIGHBOUR MAP ####################################
            
            # iterate through all points
            numPoints = tempPd1.GetNumberOfPoints()
            neighbourMap = [[] for i in range(numPoints)]
            cellIdList = vtk.vtkIdList()
            pointIdList = vtk.vtkIdList()

            for ptId in xrange(numPoints):
                # this has to be first
                neighbourMap[ptId].append(ptId)
                tempPd1.GetPointCells(ptId, cellIdList)
                # we now have all edges meeting at point i
                for cellIdListIdx in range(cellIdList.GetNumberOfIds()):
                    edgeId = cellIdList.GetId(cellIdListIdx)
                    tempPd1.GetCellPoints(edgeId, pointIdList)
                    # there have to be two points per edge,
                    # one if which is the centre-point itself
                    # FIXME: we should check, cells aren't LIMITED to two
                    # points, but could for instance be a longer line-segment
                    # or a quad or somesuch
                    for pointIdListIdx in range(pointIdList.GetNumberOfIds()):
                        tempPtId = pointIdList.GetId(pointIdListIdx)
                        if tempPtId not in neighbourMap[ptId]:
                            neighbourMap[ptId].append(tempPtId)

                #print neighbourMap[ptId]

                if ptId % (numPoints / 20) == 0:
                    self._moduleManager.setProgress(100.0 * ptId / numPoints,
                                                    "Building neighbour map")

            self._moduleManager.setProgress(100.0,
                                            "Done building neighbour map")

            # DONE BUILDING NEIGBOUR MAP ################################

            # BUILDING SEED IMAGE #######################################

            # now let's build the seed image
            # wherever we want to enforce minima, the seed image
            # should be equal to the lowest value of the mask image
            # everywhere else it should be the maximum value of the mask
            # image
            cMin, cMax = tempPd1.GetScalarRange()
            print "range: %d - %d" % (cMin, cMax)
            seedPd = vtk.vtkPolyData()
            # first make a copy of the complete PolyData
            seedPd.DeepCopy(tempPd1)
            # now change EVERYTHING to the maximum value
            print seedPd.GetPointData().GetScalars().GetName()
            # we know that the active scalars thingy has only one component,
            # namely Mean_Curvature - set it all to MAX
            seedPd.GetPointData().GetScalars().FillComponent(0, cMax)

            # now find the minima and set them too
            gPtId = seedPd.FindPoint(self._giaGlenoid)
            seedPd.GetPointData().GetScalars().SetTuple1(gPtId, cMin)
            for outsidePoint in self._outsidePoints:
                oPtId = seedPd.FindPoint(outsidePoint)
                seedPd.GetPointData().GetScalars().SetTuple1(oPtId, cMin)

            # remember vtkDataArray: array of tuples, each tuple made up
            # of n components

            # DONE BUILDING SEED IMAGE ###################################

            # MODIFY MASK IMAGE ##########################################

            # make sure that the minima as indicated by the user are cMin
            # in the mask image!

            gPtId = tempPd1.FindPoint(self._giaGlenoid)
            tempPd1.GetPointData().GetScalars().SetTuple1(gPtId, cMin)
            for outsidePoint in self._outsidePoints:
                oPtId = tempPd1.FindPoint(outsidePoint)
                tempPd1.GetPointData().GetScalars().SetTuple1(oPtId, cMin)
            
            # DONE MODIFYING MASK IMAGE ##################################


            # BEGIN erosion + supremum (modification of image homotopy)
            newSeedPd = vtk.vtkPolyData()

            newSeedPd.DeepCopy(seedPd)

            # get out some temporary variables
            tempPd1Scalars = tempPd1.GetPointData().GetScalars()
            seedPdScalars = seedPd.GetPointData().GetScalars()
            newSeedPdScalars = newSeedPd.GetPointData().GetScalars()
            
            stable = False
            iteration = 0
            while not stable:
                for nbh in neighbourMap:
                    # by definition, EACH position in neighbourmap must have
                    # at least ONE (1) ptId

                    # create list with corresponding curvatures
                    nbhC = [seedPdScalars.GetTuple1(ptId) for ptId in nbh]
                    # sort it
                    nbhC.sort()
                    # replace the centre point in newSeedPd with the lowest val
                    newSeedPdScalars.SetTuple1(nbh[0], nbhC[0])

                # now put result of supremum of newSeed and tempPd1 (the mask)
                # directly into seedPd - the loop can then continue

                # in theory, these two polydatas have identical pointdata
                # go through them, constructing newSeedPdScalars
                # while we're iterating through this loop, also check if
                # newSeedPdScalars is identical to seedPdScalars
                stable = True
                
                for i in xrange(newSeedPdScalars.GetNumberOfTuples()):
                    a = newSeedPdScalars.GetTuple1(i)
                    b = tempPd1Scalars.GetTuple1(i)
                    c = [b, a][bool(a > b)]

                    if stable and c != seedPdScalars.GetTuple1(i):
                        # we only check if stable == True
                        # if a single scalar is different, stable becomes
                        # false and we'll never have to check again
                        stable = False
                        print "unstable on point %d" % (i)
                    
                    # stuff the result directly into seedPdScalars, ready
                    # for the next iteration
                    seedPdScalars.SetTuple1(i, c)

                self._moduleManager.setProgress(iteration / 500.0 * 100.0,
                                                "Homotopic modification")
                print "iteration %d done" % (iteration)
                iteration += 1

                #if iteration == 2:
                #    stable = True

            # seedPd is the output of the homotopic modification
            # END of erosion + supremum

            # BEGIN watershed            

            pointLabels = [-1 for i in xrange(seedPd.GetNumberOfPoints())]

            # mark all minima as separate regions
            gPtId = seedPd.FindPoint(self._giaGlenoid)
            pointLabels[gPtId] = 1

            i = 1
            for outsidePoint in self._outsidePoints:
                oPtId = seedPd.FindPoint(outsidePoint)
                pointLabels[oPtId] = i * 200
                i += 1

            # now, iterate through all non-marked points
            seedPdScalars = seedPd.GetPointData().GetScalars()
            
            for ptId in xrange(seedPd.GetNumberOfPoints()):
                if pointLabels[ptId] == -1:

                    print "starting ws with ptId %d" % (ptId)
                    pathDone = False
                    # this will contain all the pointIds we walk along,
                    # starting with ptId (new path!)
                    thePath = [ptId]
                    
                    while not pathDone:

                        # now search for a neighbour with the lowest curvature
                        # but also lower than ptId itself
                        nbh = neighbourMap[thePath[-1]]
                        nbhC = [seedPdScalars.GetTuple1(pi)
                                for pi in nbh]

                        cmi = 0 # curvature minimum index cmi
                        # remember that in the neighbourhood map
                        # the "centre" point is always first
                        cms = nbhC[cmi]

                        for ci in range(len(nbhC)): # contour index ci
                            if nbhC[ci] < cms:
                                cmi = ci
                                cms = nbhC[ci]

                        if cmi != 0:
                            # this means we found a point we can move on to
                            if pointLabels[nbh[cmi]] != -1:
                                # if this is a labeled point, we know which
                                # basin thePath belongs to
                                theLabel = pointLabels[nbh[cmi]]
                                for newLabelPtId in thePath:
                                    pointLabels[newLabelPtId] = theLabel

                                print "found new path: %d (%d)" % \
                                      (theLabel, len(thePath))
                                # and our loop is done
                                pathDone = True

                            else:
                                # this is not a labeled point, which means
                                # we just add it to our path
                                thePath.append(nbh[cmi])

                        # END if cmi != 0
                        else:
                            # we couldn't find any point lower than us!

                            # let's eat as many plateau points as we can,
                            # until we reach a lower-labeled point

                            # c0 is the "current" curvature

                            plateau, plateauNeighbours, plateauLabel = \
                                     self._getPlateau(nbh[0], neighbourMap,
                                                      seedPdScalars,
                                                      pointLabels)


                            if plateauLabel != -1:
                                # this means the whole plateau is with a basin
                                for i in plateau:
                                    thePath.append(i)

                                for newLabelPtId in thePath:
                                    pointLabels[newLabelPtId] = plateauLabel

                                print "found new path: %d (%d)" % \
                                      (plateauLabel, len(thePath))
                                # and our loop is done
                                pathDone = True
                                    
                            elif not plateauNeighbours:
                                # i.e. we have a single point or a floating
                                # plateau...
                                print "floating plateau!"
                                pathDone = True
                                
                            else:
                                # now look for the lowest neighbour
                                # (c0 is the plateau scalar)
                                minScalar = cms
                                minId = -1
                                for nId in plateauNeighbours:
                                    si = seedPdScalars.GetTuple1(nId)
                                    if si < minScalar:
                                        minId = nId
                                        minScalar = si

                                if minId != -1:
                                    # this means we found the smallest
                                    # neighbour

                                    # everything on the plateau gets added to
                                    # the path
                                    for i in plateau:
                                        thePath.append(i)

                                    if pointLabels[minId] != -1:
                                        # if this is a labeled point, we know
                                        # which basin thePath belongs to
                                        theLabel = pointLabels[minId]
                                        for newLabelPtId in thePath:
                                            pointLabels[newLabelPtId] = \
                                                                      theLabel

                                        print "found new path: %d (%d)" % \
                                              (theLabel, len(thePath))
                                        # and our loop is done
                                        pathDone = True

                                    else:
                                        # this is not a labeled point, which
                                        # means we just add it to our path
                                        thePath.append(minId)
                                    
                                else:
                                    print "HELP! - we found a minimum plateau!"

            # we're done with our little path walking... now we have to assign
            # our watershedded thingy to the output data
            
            self._outputPolyDataHM.DeepCopy(seedPd)

            for ptId in xrange(len(pointLabels)):
                self._outputPolyDataHM.GetPointData().GetScalars().SetTuple1(
                    ptId,
                    pointLabels[ptId])


    def _getPlateau(self, initPt, neighbourMap, scalars, pointLabels):

        """Grow outwards from ptId nbh[0] and include all points with the
        same scalar value.

        return 2 lists: one with plateau ptIds and one with ALL the neighbour
        Ids.
        """

        # by definition, the plateau will contain at least the initial point
        plateau = [initPt]
        plateauNeighbours = []
        plateauLabel = -1
        # we're going to use this to check VERY quickly whether we've
        # already stored a point
        donePoints = [False for i in xrange(len(neighbourMap))]
        donePoints[initPt] = True
        # and this is the scalar value of the plateau
        initScalar = scalars.GetTuple1(initPt)
        # setup for loop
        currentNeighbourPts = neighbourMap[initPt]
        
        # everything in currentNeighbourPts that has equal scalar
        # gets added to plateau
        

        while currentNeighbourPts:
            newNeighbourPts = []
            for npt in currentNeighbourPts:
                if not donePoints[npt]:
                    ns = scalars.GetTuple1(npt)
                    if ns == initScalar:
                        plateau.append(npt)
                        # it could be that a point in our plateau is already
                        # labeled - check for this
                        if pointLabels[npt] != -1:
                            plateauLabel = pointLabels[npt]
                        
                    else:
                        plateauNeighbours.append(npt)

                    donePoints[npt] = True

                    # we've added a new point, now we need to get
                    # its neighbours as well
                    for i in neighbourMap[npt]:
                        newNeighbourPts.append(i)

            currentNeighbourPts = newNeighbourPts

        return (plateau, plateauNeighbours, plateauLabel)

    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()
    

    def _inputPointsObserver(self, obj):
        # extract a list from the input points
        if self._inputPoints:
            # extract the two points with labels 'GIA Glenoid'
            # and 'GIA Humerus'
            
            giaGlenoid = [i['world'] for i in self._inputPoints
                          if i['name'] == 'GIA Glenoid']

            outsidePoints = [i['world'] for i in self._inputPoints \
                            if i['name'] == 'Outside']


            if giaGlenoid and outsidePoints:
                
                # we only apply these points to our internal parameters
                # if they're valid and if they're new
                self._giaGlenoid = giaGlenoid[0]
                self._outsidePoints = outsidePoints
    
        
        
        
