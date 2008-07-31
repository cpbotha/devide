# todo:
# * vtkVolumeMapper::SetCroppingRegionPlanes(xmin,xmax,ymin,ymax,zmin,zmax)

from module_base import ModuleBase
from module_mixins import ScriptedConfigModuleMixin
import module_utils
import vtk
import vtkdevide

class VolumeRender(
    ScriptedConfigModuleMixin, ModuleBase):

    def __init__(self, module_manager):
        # initialise our base class
        ModuleBase.__init__(self, module_manager)

        # at the first config_to_logic (at the end of the ctor), this will
        # be set to 0
        self._current_rendering_type = -1

        # setup some config defaults        
        self._config.rendering_type = 0
        self._config.interpolation = 1 # linear
        self._config.ambient = 0.1
        self._config.diffuse = 0.7
        self._config.specular = 0.6
        self._config.specular_power = 80 
        self._config.threshold = 1250
        # this is not in the interface yet, change by introspection
        self._config.mip_colour = (0.0, 0.0, 1.0)
        config_list = [
            ('Rendering type:', 'rendering_type', 'base:int', 'choice',
             'Direct volume rendering algorithm that will be used.',
             ('Raycast (fixed point)', '2D Texture', '3D Texture',
                 'ShellSplatting', 'Raycast (old)')),
            ('Interpolation:', 'interpolation', 'base:int', 'choice',
             'Linear (high quality, slower) or nearest neighbour (lower '
             'quality, faster) interpolation',
             ('Nearest Neighbour', 'Linear')),
            ('Ambient:', 'ambient', 'base:float', 'text',
                'Ambient lighting term.'),
            ('Diffuse:', 'diffuse', 'base:float', 'text',
                'Diffuse lighting term.'),
            ('Specular:', 'specular', 'base:float', 'text',
                'Specular lighting term.'),
            ('Specular power:', 'specular_power', 'base:float', 'text',
                'Specular power lighting term (more focused high-lights).'),
               ('Threshold:', 'threshold', 'base:float', 'text',
             'Used to generate transfer function ONLY if none is supplied')
             ]

        ScriptedConfigModuleMixin.__init__(
            self, config_list,
            {'Module (self)' : self})

        self._input_data = None
        self._input_otf = None
        self._input_ctf = None

        self._volume_raycast_function = None
        self._create_pipeline()

        self.sync_module_logic_with_config()
            
    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for input_idx in range(len(self.get_input_descriptions())):
            self.set_input(input_idx, None)

        # this will take care of GUI
        ScriptedConfigModuleMixin.close(self)

        # get rid of our reference
        del self._volume_property
        del self._volume_raycast_function
        del self._volume_mapper
        del self._volume

    def get_input_descriptions(self):
	return ('input image data',
                'opacity transfer function',
                'colour transfer function')

    def set_input(self, idx, inputStream):
        if idx == 0:
            self._input_data = inputStream
            
        elif idx == 1:
            self._input_otf = inputStream

        else:
            self._input_ctf = inputStream

    def get_output_descriptions(self):
        return ('vtkVolume',)

    def get_output(self, idx):
        return self._volume

    def logic_to_config(self):
        self._config.rendering_type = self._current_rendering_type
        
        self._config.interpolation = \
                                   self._volume_property.GetInterpolationType()

        self._config.ambient = self._volume_property.GetAmbient()
        self._config.diffuse = self._volume_property.GetDiffuse()
        self._config.specular = self._volume_property.GetSpecular()
        self._config.specular_power = \
                self._volume_property.GetSpecularPower()

    def config_to_logic(self):
        self._volume_property.SetInterpolationType(self._config.interpolation)

        self._volume_property.SetAmbient(self._config.ambient)
        self._volume_property.SetDiffuse(self._config.diffuse)
        self._volume_property.SetSpecular(self._config.specular)
        self._volume_property.SetSpecularPower(self._config.specular_power)

        if self._config.rendering_type != self._current_rendering_type:
            if self._config.rendering_type == 0:
                # raycast fixed point
                self._setup_for_fixed_point()

            elif self._config.rendering_type == 1:
                # 2d texture
                self._setup_for_2d_texture()
                
            elif self._config.rendering_type == 2:
                # 3d texture
                self._setup_for_3d_texture()

            elif self._config.rendering_type == 3:
                # shell splatter
                self._setup_for_shell_splatting()

            else:
                # old raycaster (very picky about input types)
                self._setup_for_raycast()

            self._volume.SetMapper(self._volume_mapper)

            self._current_rendering_type = self._config.rendering_type

    def _setup_for_raycast(self):
        self._volume_raycast_function = \
                                      vtk.vtkVolumeRayCastCompositeFunction()
        
        self._volume_mapper = vtk.vtkVolumeRayCastMapper()
        self._volume_mapper.SetVolumeRayCastFunction(
            self._volume_raycast_function)
        
        module_utils.setup_vtk_object_progress(self, self._volume_mapper,
                                           'Preparing render.')

    def _setup_for_2d_texture(self):
        self._volume_mapper = vtk.vtkVolumeTextureMapper2D()
        
        module_utils.setup_vtk_object_progress(self, self._volume_mapper,
                                           'Preparing render.')

        

    def _setup_for_3d_texture(self):
        self._volume_mapper = vtk.vtkVolumeTextureMapper3D()
        
        module_utils.setup_vtk_object_progress(self, self._volume_mapper,
                                           'Preparing render.')

    def _setup_for_shell_splatting(self):
        self._volume_mapper = vtkdevide.vtkOpenGLVolumeShellSplatMapper()
        self._volume_mapper.SetOmegaL(0.9)
        self._volume_mapper.SetOmegaH(0.9)
        # high-quality rendermode
        self._volume_mapper.SetRenderMode(0)

        module_utils.setup_vtk_object_progress(self, self._volume_mapper,
                                           'Preparing render.')

    def _setup_for_fixed_point(self):
        """This doesn't seem to work.  After processing is complete,
        it stalls on actually rendering the volume.  No idea.
        """
        
        self._volume_mapper = vtk.vtkFixedPointVolumeRayCastMapper()
        self._volume_mapper.SetBlendModeToComposite()
        #self._volume_mapper.SetBlendModeToMaximumIntensity()

        module_utils.setup_vtk_object_progress(self, self._volume_mapper,
                                           'Preparing render.')
        
    def execute_module(self):
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
        ctf.AddHSVPoint(p1, 0.1, 0.7, 1.0)
        #ctf.AddHSVPoint(p2, *self._config.mip_colour)
        ctf.AddHSVPoint(p2, 0.65, 0.7, 1.0)

        return (otf, ctf)

    def _create_pipeline(self):
        # setup our pipeline

        self._volume_property = vtk.vtkVolumeProperty()
        self._volume_property.ShadeOn()

        self._volume_mapper = None

        self._volume = vtk.vtkVolume()
        self._volume.SetProperty(self._volume_property)
        self._volume.SetMapper(self._volume_mapper)

        
    
