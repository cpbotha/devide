from module_base import ModuleBase
from module_mixins import ScriptedConfigModuleMixin
import module_utils
import vtk
import vtkdevide


class imageFillHoles(ScriptedConfigModuleMixin, ModuleBase):
    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        self._imageBorderMask = vtkdevide.vtkImageBorderMask()
        # input image value for border
        self._imageBorderMask.SetBorderMode(1)
        # maximum of output for interior
        self._imageBorderMask.SetInteriorMode(3)
        
        self._imageGreyReconstruct = vtkdevide.vtkImageGreyscaleReconstruct3D()
        # we're going to use the dual, instead of inverting mask and image,
        # performing greyscale reconstruction, and then inverting the result
        # again.  (we should compare results though)
        self._imageGreyReconstruct.SetDual(1)

        # marker J is second input
        self._imageGreyReconstruct.SetInput(
            1, self._imageBorderMask.GetOutput())

        module_utils.setupVTKObjectProgress(self, self._imageBorderMask,
                                           'Creating image mask.')
        
        
        module_utils.setupVTKObjectProgress(self, self._imageGreyReconstruct,
                                           'Performing reconstruction.')
        

        self._config.holesTouchEdges = (0,0,0,0,0,0)

        configList = [
            ('Allow holes to touch edges:', 'holesTouchEdges',
             'tuple:int,6', 'text',
             'Indicate which edges (minX, maxX, minY, maxY, minZ, maxZ) may\n'
             'be touched by holes.  In other words, a hole touching such an\n'
             'edge will not be considered background and will be filled.')
            ]

        ScriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
             'vtkImageBorderMask' : self._imageBorderMask,
             'vtkImageGreyReconstruct' : self._imageGreyReconstruct})

        self.sync_module_logic_with_config()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for input_idx in range(len(self.get_input_descriptions())):
            self.set_input(input_idx, None)

        # this will take care of all display thingies
        ScriptedConfigModuleMixin.close(self)

        ModuleBase.close(self)
        
        # get rid of our reference
        del self._imageBorderMask
        del self._imageGreyReconstruct

    def get_input_descriptions(self):
        return ('VTK Image Data to be filled',)

    def set_input(self, idx, inputStream):
        self._imageBorderMask.SetInput(inputStream)
        # first input of the reconstruction is the image
        self._imageGreyReconstruct.SetInput(0, inputStream)

    def get_output_descriptions(self):
        return ('Filled VTK Image Data', 'Marker')

    def get_output(self, idx):
        if idx == 0:
            return self._imageGreyReconstruct.GetOutput()
        else:
            return self._imageBorderMask.GetOutput()

    def logic_to_config(self):
        borders = self._imageBorderMask.GetBorders()
        # if there is a border, a hole touching that edge is no hole
        self._config.holesTouchEdges = [int(not i) for i in borders]

    def config_to_logic(self):
        borders = [int(not i) for i in self._config.holesTouchEdges]
        self._imageBorderMask.SetBorders(borders)

    def execute_module(self):
        self._imageGreyReconstruct.Update()
        



    
        

    
        
                            
