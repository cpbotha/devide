import gen_utils
from module_base import ModuleBase
from module_mixins import ScriptedConfigModuleMixin
import module_utils
import vtk
import vtktudoss

class FastSurfaceToDistanceField(ScriptedConfigModuleMixin, ModuleBase):

    def __init__(self, module_manager):
        # initialise our base class
        ModuleBase.__init__(self, module_manager)

        self._clean_pd = vtk.vtkCleanPolyData()
        module_utils.setup_vtk_object_progress(
            self, self._clean_pd,
            'Cleaning up polydata')
 
        self._cpt_df = vtktudoss.vtkCPTDistanceField()
        module_utils.setup_vtk_object_progress(
            self, self._cpt_df,
            'Converting surface to distance field')
        
        # connect the up
        self._cpt_df.SetInputConnection(
                self._clean_pd.GetOutputPort())
                        
        self._config.max_dist = 1.0
        self._config.padding = 0.0
        self._config.dimensions = (64, 64, 64)
       
        configList = [
                ('Maximum distance:', 'max_dist', 'base:float',
                    'text', 
                    'Maximum distance up to which field will be '
                    'calculated.'),
                ('Dimensions:', 'dimensions', 'tuple:int,3',
                    'tupleText',
                    'Resolution of resultant distance field.'),
                ('Padding:', 'padding', 'base:float', 'text',
                    'Padding of distance field around surface.')]

        ScriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
                'vtkCleanPolyData' : self._clean_pd,
                'vtkCPTDistanceField' : self._cpt_df})

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
        del self._clean_pd
        del self._cpt_df

    def get_input_descriptions(self):
        return ('Surface (vtkPolyData)',)

    def set_input(self, idx, inputStream):
        self._clean_pd.SetInput(inputStream)
        
    def get_output_descriptions(self):
        return ('Distance field (VTK Image Data)',)

    def get_output(self, idx):
        return self._cpt_df.GetOutput()

    def logic_to_config(self):
        self._config.max_dist = self._cpt_df.GetMaximumDistance()
        self._config.padding = self._cpt_df.GetPadding()
        self._config.dimensions = self._cpt_df.GetDimensions()
       
    def config_to_logic(self):
        self._cpt_df.SetMaximumDistance(self._config.max_dist)
        self._cpt_df.SetPadding(self._config.padding)
        self._cpt_df.SetDimensions(self._config.dimensions)

    def execute_module(self):
        self._cpt_df.Update()


