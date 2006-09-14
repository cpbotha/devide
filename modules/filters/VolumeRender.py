# todo:
# * vtkVolumeMapper::SetCroppingRegionPlanes(xmin,xmax,ymin,ymax,zmin,zmax)

from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtk

class VolumeRender(
    scriptedConfigModuleMixin, moduleBase):

    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)

        # at the first configToLogic (at the end of the ctor), this will
        # be set to 0
        self._current_rendering_type = -1

        # setup some config defaults        
        self._config.rendering_type = 0
        self._config.threshold = 1250
        self._config.interpolation = 0 # nearest
        # this is not in the interface yet, change by introspection
        self._config.mip_colour = (0.0, 0.0, 1.0)
        config_list = [
            ('Rendering type:', 'rendering_type', 'base:int', 'choice',
             'Direct volume rendering algorithm that will be used.',
             ('Raycast', '2D Texture', '3D Texture')),
            ('Threshold:', 'threshold', 'base:float', 'text',
             'Used to generate transfer function if none is supplied'),
            ('Interpolation:', 'interpolation', 'base:int', 'choice',
             'Linear (high quality, slower) or nearest neighbour (lower '
             'quality, faster) interpolation',
             ('Nearest Neighbour', 'Linear'))]

        scriptedConfigModuleMixin.__init__(self, config_list)
        
        self._createWindow(
            {'Module (self)' : self})

        self._input_data = None
        self._input_otf = None
        self._input_ctf = None

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
        del self._volume_property
        del self._volume_raycast_function
        del self._volume_mapper
        del self._volume

    def getInputDescriptions(self):
	return ('input image data',
                'opacity transfer function',
                'colour transfer function')

    def setInput(self, idx, inputStream):
        if idx == 0:
            self._input_data = inputStream
            
        elif idx == 1:
            self._input_otf = inputStream

        else:
            self._input_ctf = inputStream

    def getOutputDescriptions(self):
        return ('vtkVolume',)

    def getOutput(self, idx):
        return self._volume

    def logicToConfig(self):
        self._config.rendering_type = self._current_rendering_type
        
        self._config.interpolation = \
                                   self._volume_property.GetInterpolationType()

    def configToLogic(self):
        self._volume_property.SetInterpolationType(self._config.interpolation)

        if self._config.rendering_type != self._current_rendering_type:
            if self._config.rendering_type == 0:
                # raycast
                self._setup_for_raycast()

            elif self._config.rendering_type == 1:
                # 2d texture
                self._setup_for_2d_texture()
                
            else:
                # 3d texture
                self._setup_for_3d_texture()

            self._volume.SetMapper(self._volume_mapper)

            self._current_rendering_type = self._config.rendering_type

    def _setup_for_raycast(self):
        self._volume_raycast_function = \
                                      vtk.vtkVolumeRayCastCompositeFunction()
        
        self._volume_mapper = vtk.vtkVolumeRayCastMapper()
        self._volume_mapper.SetVolumeRayCastFunction(
            self._volume_raycast_function)
        
        moduleUtils.setupVTKObjectProgress(self, self._volume_mapper,
                                           'Preparing render.')

    def _setup_for_2d_texture(self):
        self._volume_mapper = vtk.vtkVolumeTextureMapper2D()
        
        moduleUtils.setupVTKObjectProgress(self, self._volume_mapper,
                                           'Preparing render.')

        

    def _setup_for_3d_texture(self):
        self._volume_mapper = vtk.vtkVolumeTextureMapper3D()
        
        moduleUtils.setupVTKObjectProgress(self, self._volume_mapper,
                                           'Preparing render.')

    def executeModule(self):
        otf, ctf = self._create_tfs()
        
        if self._input_otf is not None:
            otf = self._input_otf

        if self._input_ctf is not None:
            ctf = self._input_ctf

        self._volume_property.SetScalarOpacity(otf)
        self._volume_property.SetColor(ctf)

        self._volume_mapper.SetInput(self._input_data)

        self._volume_mapper.Update()
        
    def _create_tfs(self):
        otf = vtk.vtkPiecewiseFunction()
        ctf = vtk.vtkColorTransferFunction()

        otf.RemoveAllPoints()
        t = self._config.threshold
        p1 = t - t / 10.0
        p2 = t + t / 5.0
        print "MIP: %.2f - %.2f" % (p1, p2)
        otf.AddPoint(p1, 0.0)
        otf.AddPoint(p2, 1.0)
        otf.AddPoint(self._config.threshold, 1.0)
        
        ctf.RemoveAllPoints()
        ctf.AddHSVPoint(p1, 0.0, 0.0, 0.0)
        ctf.AddHSVPoint(p2, *self._config.mip_colour)

        return (otf, ctf)

    def _create_pipeline(self):
        # setup our pipeline

        self._volume_property = vtk.vtkVolumeProperty()
        self._volume_property.ShadeOn()
        self._volume_property.SetAmbient(0.1)
        self._volume_property.SetDiffuse(0.7)
        self._volume_property.SetSpecular(0.2)
        self._volume_property.SetSpecularPower(10)

        self._volume_mapper = None

        self._volume = vtk.vtkVolume()
        self._volume.SetProperty(self._volume_property)
        self._volume.SetMapper(self._volume_mapper)

        
    
