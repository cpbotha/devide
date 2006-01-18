# pointsToSpheres.py copyright (c) 2005 by Charl P. Botha <cpbotha@ieee.org>
# $Id$
# see module documentation

# FIXME: the observer pattern is not required anymore in the new event-driven
# model.

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

    Each point's sphere has an array associated to its pointdata called
    'VolumeIndex'.  All values in this array are equal to the corresponding
    point's index in the input points list.

    $Revision: 1.6 $

    @author: Charl P. Botha <http://cpbotha.net/>
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

        # and a dummy calc, with -1 index
        # if we don't add the VolumeIndex array here as well, the append
        # polydata discards all the others
        calc = vtk.vtkArrayCalculator()
        calc.SetAttributeModeToUsePointData()
        calc.SetFunction('-1')
        calc.SetResultArrayName('VolumeIndex')
        calc.SetInput(dummySphere.GetOutput())
        
        self._appendPolyData.AddInput(calc.GetOutput())
        # this will be a list of lists containing tuples
        # (vtkArrayCalculator, vtkSphereSource)
        self._sphereSources = []

        # this will hold our shallow-copied output
        self._output = vtk.vtkPolyData()

        self._createWindow(
            {'Module (self)' : self,
             'vtkAppendPolyData' : self._appendPolyData})

        self.configToLogic()
        self.logicToConfig()
        self.configToView()

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
        del self._output

    def getInputDescriptions(self):
        return ('Selected points',)

    def setInput(self, idx, inputStream):
        if inputStream is not self._inputPoints:

            if inputStream == None:
                self._inputPoints = None

            elif hasattr(inputStream, 'devideType') and \
                     inputStream.devideType == 'namedPoints':
                # correct type
                self._inputPoints = inputStream
                # initial update
                #self._observerInputPoints(None)

            else:
                raise TypeError, 'This input requires a named points type.'

    def getOutputDescriptions(self):
        return ('PolyData spheres',)

    def getOutput(self, idx):
        #return self._appendPolyData.GetOutput()
        return self._output

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
                    # each element of spheres is a (calc, sphere) tuple
                    sphere = spheres[i][1]
                    sphere.SetRadius(self._config.radius - radiusStep * i)
                    sphere.SetThetaResolution(self._config.thetaResolution)
                    sphere.SetPhiResolution(self._config.phiResolution)
    
    def executeModule(self):
        # synchronise our balls on the input points (they might have changed)
        self._syncOnInputPoints()
        # run the whole pipeline
        self._appendPolyData.Update()

        # shallow copy the polydata
        self._output.ShallowCopy(self._appendPolyData.GetOutput())
        # indicate that the output has been modified
        self._output.Modified()

    def _syncOnInputPoints(self):
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
                    for calc,sphere in self._sphereSources[i]:
                        # set new centre
                        sphere.SetCenter(pt)
                        # set new index!
                        calc.SetFunction('%d' % (i,))

            else:
                # if the number of points HAS changed, we have to redo
                # everything (we could try figuring out how things have
                # changed, but we won't)
                self._createSpheres()

    def _destroySpheres(self):
        # first remove all inputs from the appender
        for spheres in self._sphereSources:
            for calc, sphere in spheres:
                self._appendPolyData.RemoveInput(calc.GetOutput())

        # now actually nuke our references
        del self._sphereSources[:]
        
    def _createSpheres(self):
        """Create all spheres according to self._internalPoints.
        """
        
        # make sure we're all empty
        self._destroySpheres()
        
        for ptIdx in range(len(self._internalPoints)):
            pt = self._internalPoints[ptIdx]
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

                # use calculator to add array with VolumeIndex
                calc = vtk.vtkArrayCalculator()
                calc.SetAttributeModeToUsePointData()
                calc.SetFunction('%d' % (ptIdx,))
                calc.SetResultArrayName('VolumeIndex')
                calc.SetInput(sphere.GetOutput())

                self._appendPolyData.AddInput(calc.GetOutput())
                spheres.append((calc,sphere))
                
            self._sphereSources.append(spheres)

    def _getRadiusStep(self):
        radiusStep = self._config.radius / \
                     float(self._config.numInternalSpheres + 1)
        return radiusStep
