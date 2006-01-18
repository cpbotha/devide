# surfaceToDistanceField copyright (c) 2004 by Charl P. Botha cpbotha.net
# $Id$

import genUtils
from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtk

class surfaceToDistanceField(scriptedConfigModuleMixin, moduleBase):

    """Given an input surface (vtkPolyData), create an unsigned distance field
    with the surface at distance 0.

    The user must specify the dimensions and bounds of the output volume.

    WARNING: this filter is *incredibly* slow, even for small volumes and
    extremely simple geometry.  Only use this if you know exactly what
    you're doing.
    
    $Revision: 1.2 $
    """

    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)


        self._implicitModeller = vtk.vtkImplicitModeller()
        moduleUtils.setupVTKObjectProgress(
            self, self._implicitModeller,
            'Converting surface to distance field')
                                           
        self._config.bounds = (-1, 1, -1, 1, -1, 1)
        self._config.dimensions = (64, 64, 64)
        self._config.maxDistance = 0.1
        

        configList = [
            ('Bounds:', 'bounds', 'tuple:float,6', 'text',
             'The physical location of the sampled volume in space '
             '(x0, x1, y0, y1, z0, z1)'),
            ('Dimensions:', 'dimensions', 'tuple:int,3', 'text',
             'The number of points that should be sampled in each dimension.'),
            ('Maximum distance:', 'maxDistance', 'base:float', 'text',
             'The distance will only be calculated up to this maximum.')]

        scriptedConfigModuleMixin.__init__(self, configList)        

        self._viewFrame = self._createWindow(
            {'Module (self)' : self,
             'vtkImplicitModeller' : self._implicitModeller})

        # pass the data down to the underlying logic
        self.configToLogic()
        # and all the way up from logic -> config -> view to make sure
        self.logicToConfig()
        self.configToView()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)

        moduleBase.close(self)
        
        # get rid of our reference
        del self._implicitModeller

    def getInputDescriptions(self):
        return ('Surface (vtkPolyData)',)

    def setInput(self, idx, inputStream):
        self._implicitModeller.SetInput(inputStream)
        
    def getOutputDescriptions(self):
        return ('Distance field (VTK Image Data)',)

    def getOutput(self, idx):
        return self._implicitModeller.GetOutput()

    def logicToConfig(self):
        self._config.bounds = self._implicitModeller.GetModelBounds()
        self._config.dimensions = self._implicitModeller.GetSampleDimensions()
        self._config.maxDistance = self._implicitModeller.GetMaximumDistance()
        
    def configToLogic(self):
        self._implicitModeller.SetModelBounds(self._config.bounds)
        self._implicitModeller.SetSampleDimensions(self._config.dimensions)
        self._implicitModeller.SetMaximumDistance(self._config.maxDistance)
    
    def executeModule(self):
        self._implicitModeller.Update()


