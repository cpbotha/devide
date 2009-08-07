import gen_utils
from module_base import ModuleBase
from module_mixins import ScriptedConfigModuleMixin
import module_utils
import vtk

EMODES = { 
        1:'Point seeded regions',
        2:'Cell seeded regions',
        3:'Specified regions',
        4:'Largest region',
        5:'All regions',
        6:'Closest point region'
        }


class polyDataConnect(ScriptedConfigModuleMixin, ModuleBase):

    def __init__(self, module_manager):

        # call parent constructor
        ModuleBase.__init__(self, module_manager)

        self._polyDataConnect = vtk.vtkPolyDataConnectivityFilter()
        # we're not going to use this feature just yet
        self._polyDataConnect.ScalarConnectivityOff()
        #
        self._polyDataConnect.SetExtractionModeToPointSeededRegions()

        module_utils.setup_vtk_object_progress(self, self._polyDataConnect,
                                           'Finding connected surfaces')

        # default is point seeded regions (we store zero-based)
        self._config.extraction_mode = 0
        self._config.colour_regions = 0

        config_list = [
                ('Extraction mode:', 'extraction_mode', 'base:int',
                 'choice', 
                 'What kind of connected regions should be extracted.',
                 [EMODES[i] for i in range(1,7)]),
                ('Colour regions:', 'colour_regions', 'base:int',
                 'checkbox', 
                 'Should connected regions be coloured differently.')
                ]
        
        # and the mixin constructor
        ScriptedConfigModuleMixin.__init__(
            self, config_list,
            {'Module (self)' : self,
             'vtkPolyDataConnectivityFilter' : self._polyDataConnect})

        # we'll use this to keep a binding (reference) to the passed object
        self._input_points = None
        # this will be our internal list of points
        self._seedIds = []

        self.sync_module_logic_with_config()
        
    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        self.set_input(0, None)
        # don't forget to call the close() method of the vtkPipeline mixin
        ScriptedConfigModuleMixin.close(self)
        ModuleBase.close(self)
        # get rid of our reference
        del self._polyDataConnect

    def get_input_descriptions(self):
        return ('vtkPolyData', 'Seed points')
    
    def set_input(self, idx, inputStream):
        if idx == 0:
            # will work for None and not-None
            self._polyDataConnect.SetInput(inputStream)
        else:
            self._input_points = inputStream
    
    def get_output_descriptions(self):
        return (self._polyDataConnect.GetOutput().GetClassName(),)
    
    def get_output(self, idx):
        return self._polyDataConnect.GetOutput()

    def logic_to_config(self):
        # extractionmodes in vtkPolyDataCF start at 1
        # we store it as 0-based
        emode = self._polyDataConnect.GetExtractionMode()
        self._config.extraction_mode = emode - 1
        self._config.colour_regions = \
                self._polyDataConnect.GetColorRegions()

    def config_to_logic(self):
        # extractionmodes in vtkPolyDataCF start at 1
        # we store it as 0-based
        self._polyDataConnect.SetExtractionMode(
                self._config.extraction_mode + 1)
        self._polyDataConnect.SetColorRegions(
                self._config.colour_regions)
    
    def execute_module(self):
        if self._polyDataConnect.GetExtractionMode() == 1:
            self._sync_pdc_to_input_points()

        self._polyDataConnect.Update()
        
    def _sync_pdc_to_input_points(self):
        # extract a list from the input points
        temp_list = []
        if self._input_points and self._polyDataConnect.GetInput():
            for i in self._input_points:
                id = self._polyDataConnect.GetInput().FindPoint(i['world'])
                if id > 0:
                    temp_list.append(id)
            
        if temp_list != self._seedIds:
            self._seedIds = temp_list
            # I'm hoping this clears the list
            self._polyDataConnect.InitializeSeedList()
            for seedId in self._seedIds:
                self._polyDataConnect.AddSeed(seedId)
                print "adding %d" % (seedId)



