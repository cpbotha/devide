# landmarkTransform.py copyright (c) 2003 by Charl P. Botha <cpbotha@ieee.org>
# $Id: pointsToSpheres.py,v 1.1 2004/11/21 22:03:54 cpbotha Exp $
# see module documentation

import genUtils
from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import wx
import vtk

class pointsToSpheres(scriptedConfigModuleMixin, moduleBase):
    """Given a set of selected points (for instance from a slice3dVWR),
    generate polydata spheres centred at these points with user-specified
    radius.  The spheres' interiors are filled with smaller spheres.  This is
    useful when using selected points to generate points for seeding
    streamlines or calculating advection by a vector field.

    $Revision: 1.1 $
    """

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        self._inputPoints = None
        self._internalPoints = None

        self._config.radius = 5
        self._config.thetaResolution = 8 # minimum 3
        self._config.phiResolution = 8 # minimum 3
        self._config.numInternalSpheres = 3

        configList = [('Sphere radius:', 'radius', 'base:float', 'text',
                       'The radius of the spheres that will be created '
                       'in world coordinate units.'),
                      ('Theta resolution:', 'thetaResolution', 'base:int',
                       'text',
                       'Number of points in the longitudinal direction.'),
                      ('Phi resolution:', 'phiResolution', 'base:int',
                       'text',
                       'Number of points in the latitudinal direction.'),
                      ('Number of internal spheres:', 'numInternalSpheres',
                       'base:int', 'text',
                       'Number of spheres to create in the interior.')]

        scriptedConfigModuleMixin.__init__(self, configList)

        self._appendPolyData = vtk.vtkAppendPolyData()
        # we do need a dummy sphere, else the appender complains
        dummySphere = vtk.vtkSphereSource()
        dummySphere.SetRadius(0.0)
        self._appendPolyData.AddInput(dummySphere.GetOutput())
        # this will be a list of lists
        self._sphereSources = []

        self._createWindow(
            {'Module (self)' : self,
             'all vtkSphereSources': self._sphereSources,
             'vtkAppendPolyData' : self._appendPolyData})

        self.configToLogic()
        self.syncViewWithLogic()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)
        
        # get rid of our reference
        del self._appendPolyData
        del self._sphereSources

    def getInputDescriptions(self):
        return ('Selected points',)

    def setInput(self, idx, inputStream):
        if inputStream is not self._inputPoints:

            if inputStream == None:
                # disconnect
                if self._inputPoints:
                    self._inputPoints.removeObserver(
                        self._observerInputPoints)
                    
                self._inputPoints = None

            elif hasattr(inputStream, 'devideType') and \
                 inputStream.devideType == 'namedPoints':
                # correct type... first disconnect the old
                if self._inputPoints:
                    self._inputPoints.removeObserver(
                        self._observerInputPoints)

                self._inputPoints = inputStream
                self._inputPoints.addObserver(self._observerInputPoints)

                # initial update
                self._observerInputPoints(None)

            else:
                raise TypeError, 'This input requires a named points type.'

    def getOutputDescriptions(self):
        return ('PolyData spheres',)

    def getOutput(self, idx):
            return self._appendPolyData.GetOutput()

    def logicToConfig(self):
        pass
    
    def configToLogic(self):
        # if any of the parameters have changed, this affects all the spheres
        # fortunately VTK caches this type of parameter so we don't have to
        # check

        # some sanity checking
        if self._config.radius < 0:
            self._config.radius = 0
        
        if self._config.thetaResolution < 3:
            self._config.thetaResolution = 3

        if self._config.phiResolution < 3:
            self._config.phiResolution = 3
        
        if self._config.numInternalSpheres < 0:
            self._config.numInternalSpheres = 0



        # if the number of internal spheres has changed, we have to start over
        haveToCreate = False
        if len(self._sphereSources) > 0:
            # this means we HAVE spheres already
            currentNum = len(self._sphereSources[0]) - 1
            if currentNum != self._config.numInternalSpheres:
                haveToCreate = True

        if haveToCreate:
            self._createSpheres()

        else:
            radiusStep = self._getRadiusStep()
        
            for spheres in self._sphereSources:
                for i in range(len(spheres)):
                    sphere = spheres[i]
                    sphere.SetRadius(self._config.radius - radiusStep * i)
                    sphere.SetThetaResolution(self._config.thetaResolution)
                    sphere.SetPhiResolution(self._config.phiResolution)
    
    def executeModule(self):
        self.getOutput(0).Update()

    def _observerInputPoints(self, obj):
        # extract a list from the input points
        tempList = []
        if self._inputPoints:
            for i in self._inputPoints:
                tempList.append(i['world'])

        if tempList != self._internalPoints:

            # store the new points
            self._internalPoints = tempList

            if len(self._internalPoints) == len(self._sphereSources):
                # if the number of points has not changed, we only have to
                # move points
                for i in range(len(self._internalPoints)):
                    pt = self._internalPoints[i]
                    for sphere in self._sphereSources[i]:
                        sphere.SetCenter(pt)

            else:
                # if the number of points HAS changed, we have to redo
                # everything (we could try figuring out how things have
                # changed, but we won't)
                self._createSpheres()

    def _destroySpheres(self):
        # first remove all inputs from the appender
        for spheres in self._sphereSources:
            for sphere in spheres:
                self._appendPolyData.RemoveInput(sphere.GetOutput())

        # now actually nuke our references
        del self._sphereSources[:]
        
    def _createSpheres(self):
        """Create all spheres according to self._internalPoints.
        """
        
        if len(self._internalPoints) == 0:
            return

        # make sure we're all empty
        self._destroySpheres()
        
        for pt in self._internalPoints:
            # each point gets potentially more than one sphere
            spheres = []

            # then create and add the internal spheres
            radiusStep = self._getRadiusStep()

            # we do the mainSphere and the internal spheres in one go
            for i in range(self._config.numInternalSpheres + 1):
                sphere = vtk.vtkSphereSource()
                sphere.SetCenter(pt)
                sphere.SetRadius(self._config.radius - radiusStep * i)
                sphere.SetThetaResolution(self._config.thetaResolution)
                sphere.SetPhiResolution(self._config.phiResolution)

                self._appendPolyData.AddInput(sphere.GetOutput())
                spheres.append(sphere)
                
            self._sphereSources.append(spheres)

    def _getRadiusStep(self):
        radiusStep = self._config.radius / \
                     float(self._config.numInternalSpheres + 1)
        return radiusStep
