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

        self._tf = vtk.vtkTriangleFilter()
        self._curvatures = vtk.vtkCurvatures()
        self._curvatures.SetCurvatureTypeToMean()        
        self._curvatures.SetInput(self._tf.GetOutput())

        mm = self._moduleManager
        self._tf.SetProgressText('triangulating')
        self._tf.SetProgressMethod(lambda s=self, mm=mm:
                                   mm.vtk_progress_cb(s._tf))

        self._curvatures.SetProgressText('calculating curvatures')
        self._curvatures.SetProgressMethod(lambda s=self, mm=mm:
                                           mm.vtk_progress_cb(s._curvatures))

        self._inputPoints = None
        self._inputPointsOID = None

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
        del self._curvatures
        del self._tf

    def getInputDescriptions(self):
	return ('vtkPolyData', 'Watershed minima')

    def setInput(self, idx, inputStream):
        if idx == 0:
            self._tf.SetInput(inputStream)
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
        return ()

    def getOutput(self, idx):
        return None

    def logicToConfig(self):
        pass

    def configToLogic(self):
        pass

    def viewToConfig(self):
        pass

    def configToView(self):
        pass
    

    def executeModule(self):
        if self._tf.GetInput():
            self._curvatures.Update()
            # vtkCurvatures has added a mean curvature array to the
            # pointData of the output polydata

            pd = self._curvatures.GetOutput()

            # make a deep copy of the data that we can work with
            tempPd1 = vtk.vtkPolyData()
            tempPd1.DeepCopy(self._curvatures.GetOutput())

            # BUILDING NEIGHBOUR MAP ####################################
            
            # iterate through all points
            numPoints = tempPd1.GetNumberOfPoints()
            neighbourMap = [[] for i in range(numPoints)]
            cellIdList = vtk.vtkIdList()
            pointIdList = vtk.vtkIdList()

            for ptId in range(numPoints):
                tempPd1.GetPointCells(ptId, cellIdList)
                # we now have all edges meeting at point i
                for cellIdListIdx in range(cellIdList.GetNumberOfIds()):
                    edgeId = cellIdList.GetId(cellIdListIdx)
                    tempPd1.GetCellPoints(edgeId, pointIdList)
                    # there have to be two points per edge,
                    # one if which is the centre-point itself
                    for pointIdListIdx in range(pointIdList.GetNumberOfIds()):
                        tempPtId = pointIdList.GetId(pointIdListIdx)
                        if tempPtId not in neighbourMap[ptId]:
                            
                            neighbourMap[ptId].append(tempPtId)

                if ptId % (numPoints / 20) == 0:
                    self._moduleManager.setProgress(100.0 * ptId / numPoints,
                                                    "Building neighbour map")

            self._moduleManager.setProgress(100.0,
                                            "Done building neighbour map")

            # DONE BUILDING NEIGBOUR MAP ################################

            print tempPd1.GetScalarRange()
            # the curvature data is unsigned, let's try and change that
            tempPd1.GetPointData().GetArray("Mean_Curvature")

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

            outside = [i['world'] for i in self._inputPoints
                       if i['name'] == 'Outside']


            if giaGlenoid and outside:
                
                # we only apply these points to our internal parameters
                # if they're valid and if they're new
                self._giaGlenoid = giaGlenoid[0]
                self._outsidePoint = outside[0]
    
        
        
        
