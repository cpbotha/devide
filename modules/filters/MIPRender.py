# todo:
# * vtkVolumeMapper::SetCroppingRegionPlanes(xmin,xmax,ymin,ymax,zmin,zmax)

from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtk


class MIPRender(
    scriptedConfigModuleMixin, moduleBase):

    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)

        #for o in self._objectDict.values():
        #    

        # setup some config defaults
        self._config.threshold = 1250
        self._config.interpolation = 0 # nearest
        # this is not in the interface yet, change by introspection
        self._config.mip_colour = (0.0, 0.0, 1.0)
        config_list = [
            ('Threshold:', 'threshold', 'base:float', 'text',
             'Used to generate transfer function if none is supplied'),
            ('Interpolation:', 'interpolation', 'base:int', 'choice',
             'Linear (high quality, slower) or nearest neighbour (lower '
             'quality, faster) interpolation',
             ('Nearest Neighbour', 'Linear'))]

        scriptedConfigModuleMixin.__init__(self, config_list)
        
        self._createWindow(
            {'Module (self)' : self})

        self._create_pipeline()

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

        # this will take care of GUI
        scriptedConfigModuleMixin.close(self)

        # get rid of our reference
        del self._otf
        del self._ctf
        del self._volume_property
        del self._volume_raycast_function
        del self._volume_mapper
        del self._volume

    def getInputDescriptions(self):
	return ('input image data', 'transfer functions')

    def setInput(self, idx, inputStream):
        if idx == 0:
            self._volume_mapper.SetInput(inputStream)
            
        else:
            pass

    def getOutputDescriptions(self):
        return ('vtkVolume',)

    def getOutput(self, idx):
        return self._volume

    def logicToConfig(self):
        self._config.interpolation = \
                                   self._volume_property.GetInterpolationType()

    def configToLogic(self):

        self._otf.RemoveAllPoints()
        t = self._config.threshold
        p1 = t - t / 10.0
        p2 = t + t / 5.0
        print "MIP: %.2f - %.2f" % (p1, p2)
        self._otf.AddPoint(p1, 0.0)
        self._otf.AddPoint(p2, 1.0)
        self._otf.AddPoint(self._config.threshold, 1.0)
        
        self._ctf.RemoveAllPoints()
        self._ctf.AddHSVPoint(p1, 0.0, 0.0, 0.0)
        self._ctf.AddHSVPoint(p2, *self._config.mip_colour)

        self._volume_property.SetInterpolationType(self._config.interpolation)

    def executeModule(self):
        self._volume_mapper.Update()
        


    def _create_pipeline(self):
        # setup our pipeline

        self._otf = vtk.vtkPiecewiseFunction()
        self._ctf = vtk.vtkColorTransferFunction()

        self._volume_property = vtk.vtkVolumeProperty()
        self._volume_property.SetScalarOpacity(self._otf)
        self._volume_property.SetColor(self._ctf)
        self._volume_property.ShadeOn()
        self._volume_property.SetAmbient(0.1)
        self._volume_property.SetDiffuse(0.7)
        self._volume_property.SetSpecular(0.2)
        self._volume_property.SetSpecularPower(10)

        self._volume_raycast_function = vtk.vtkVolumeRayCastMIPFunction()
        self._volume_mapper = vtk.vtkVolumeRayCastMapper()

        # can also used FixedPoint, but then we have to use:
        # SetBlendModeToMaximumIntensity() and not SetVolumeRayCastFunction
        #self._volume_mapper = vtk.vtkFixedPointVolumeRayCastMapper()
        
        self._volume_mapper.SetVolumeRayCastFunction(
            self._volume_raycast_function)

        
        moduleUtils.setupVTKObjectProgress(self, self._volume_mapper,
                                           'Preparing render.')

        self._volume = vtk.vtkVolume()
        self._volume.SetProperty(self._volume_property)
        self._volume.SetMapper(self._volume_mapper)

        
    
