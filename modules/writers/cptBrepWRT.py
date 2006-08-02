# $Id$

from moduleBase import moduleBase
from moduleMixins import filenameViewModuleMixin
import moduleUtils
import vtk


class cptBrepWRT(moduleBase, filenameViewModuleMixin):
    """Writes polydata to disc in the format required by the Closest
    Point Transform (CPT) driver software.  Input data is put through
    a triangle filter first, as that is what the CPT requires.

    See the
    <a href="http://www.acm.caltech.edu/~seanm/projects/cpt/cpt.html">CPT
    home page</a> for more information about the algorithm and the
    software.

    $Revision: 1.3 $
    """

    def __init__(self, moduleManager):

        # call parent constructor
        moduleBase.__init__(self, moduleManager)
        # ctor for this specific mixin
        filenameViewModuleMixin.__init__(self)

        self._triFilter = vtk.vtkTriangleFilter()

        moduleUtils.setupVTKObjectProgress(
            self, self._triFilter,
            'Converting to triangles')

        

        # we now have a viewFrame in self._viewFrame
        self._createViewFrame('Select a filename',
                              'brep files (*.brep)|*.brep|All files (*)|*',
                              {'Module (self)' : self,
                               'vtkTriangleFilter': self._triFilter},
                              fileOpen=False)

        # set up some defaults
        self._config.filename = ''
        self.configToLogic()
        # make sure these filter through from the bottom up
        self.logicToConfig()
        self.configToView()

    def close(self):
        # we should disconnect all inputs
        self.setInput(0, None)
        del self._triFilter
        filenameViewModuleMixin.close(self)

    def getInputDescriptions(self):
	return ('vtkPolyData',)
    
    def setInput(self, idx, inputStream):
        self._triFilter.SetInput(inputStream)
    
    def getOutputDescriptions(self):
	return ()
    
    def getOutput(self, idx):
        raise Exception
    
    def logicToConfig(self):
        pass

    def configToLogic(self):
        pass

    def viewToConfig(self):
        self._config.filename = self._getViewFrameFilename()

    def configToView(self):
        self._setViewFrameFilename(self._config.filename)

    def executeModule(self):
        if len(self._config.filename) and self._triFilter.GetInput():

            # make sure our input is up to date
            polyData = self._triFilter.GetOutput()
            polyData.Update()

            # this will throw an exception if something went wrong.
            
            
            # list of tuples, each tuple contains three indices into vertices
            # list constituting a triangle face
            faces = []

            self._moduleManager.setProgress(10,'Extracting triangles')
            # blaat.
            numCells = polyData.GetNumberOfCells()
            for cellIdx in xrange(numCells):
                c = polyData.GetCell(cellIdx)
                # make sure we're working with triangles
                if c.GetClassName() == 'vtkTriangle':
                    pointIds = c.GetPointIds()
                    if pointIds.GetNumberOfIds() == 3:
                        faces.append((pointIds.GetId(0), pointIds.GetId(1),
                                      pointIds.GetId(2)))

            # now we can finally write
            f = file(self._config.filename, 'w')
            f.write('%d\n%d\n' % (polyData.GetNumberOfPoints(), len(faces)))

            numPoints = polyData.GetNumberOfPoints()
            for ptIdx in xrange(numPoints):
                # polyData.GetPoint() returns a 3-tuple
                f.write('%f %f %f\n' % polyData.GetPoint(ptIdx))

                pp = ptIdx / numPoints * 100.0
                if pp % 10 == 0:
                    self._moduleManager.setProgress(
                        pp, 'Writing points')

            numFaces = len(faces)
            faceIdx = 0
            for face in faces:
                f.write('%d %d %d\n' % face)

                # this is just for progress
                faceIdx += 1

                pp = faceIdx / numFaces * 100.0
                if pp % 10 == 0:
                    self._moduleManager.setProgress(
                        pp, 'Writing triangles')
            

    def view(self, parent_window=None):
        self._viewFrame.Show(True)
        self._viewFrame.Raise()
