# Modified by FrancoisMalan 2011-12-06 so that it can handle an input with larger 
# extent than its source. Changes constitute the padder module and pad_source method

import gen_utils
from module_base import ModuleBase
from module_mixins import NoConfigModuleMixin
import module_utils
import vtk


class probeFilter(NoConfigModuleMixin, ModuleBase):
    def __init__(self, module_manager):
        # initialise our base class
        ModuleBase.__init__(self, module_manager)

        # what a lame-assed filter, we have to make dummy inputs!
        # if we don't have a dummy input (but instead a None input) it
        # bitterly complains when we do a GetOutput() (it needs the input
        # to know the type of the output) - and GetPolyDataOutput() also
        # doesn't work.
        # NB: this does mean that our probeFilter NEEDS a PolyData as
        # probe geometry!
        ss = vtk.vtkSphereSource()
        ss.SetRadius(0)
        self._dummyInput = ss.GetOutput()

        #This is also retarded - we (sometimes, see below) need the "padder"
        #to get the image extent big enough to satisfy the probe filter. 
        #No apparent logical reason, but it throws an exception if we don't.
        self._padder = vtk.vtkImageConstantPad()
        self._source = None
        self._input = None
        
        self._probeFilter = vtk.vtkProbeFilter()
        self._probeFilter.SetInput(self._dummyInput)

        NoConfigModuleMixin.__init__(
            self,
            {'Module (self)' : self,
             'vtkProbeFilter' : self._probeFilter})

        module_utils.setup_vtk_object_progress(self, self._probeFilter,
                                           'Mapping source on input')
        
        self.sync_module_logic_with_config()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for input_idx in range(len(self.get_input_descriptions())):
            self.set_input(input_idx, None)

        # this will take care of all display thingies
        NoConfigModuleMixin.close(self)
        
        # get rid of our reference
        del self._probeFilter
        del self._dummyInput
        del self._padder
        del self._source
        del self._input

    def get_input_descriptions(self):
        return ('Input', 'Source')

    def set_input(self, idx, inputStream):
        if idx == 0:
            self._input = inputStream
        else:
            self._source = inputStream

    def get_output_descriptions(self):
        return ('Input with mapped source values',)

    def get_output(self, idx):
        return self._probeFilter.GetOutput()

    def logic_to_config(self):
        pass
    
    def config_to_logic(self):
        pass
    
    def view_to_config(self):
        pass

    def config_to_view(self):
        pass
    
    def pad_source(self):
        input_extent = self._input.GetExtent()
        source_extent = self._source.GetExtent()
    
        if (input_extent[0] < source_extent[0]) or (input_extent[2] < source_extent[2]) or (input_extent[4] < source_extent[4]):
            raise Exception('Output extent starts at lower index than source extent. Assumed that both should be zero?')
        elif (input_extent[1] > source_extent[1]) or (input_extent[3] > source_extent[3]) or (input_extent[5] > source_extent[5]):
            extX = max(input_extent[1], source_extent[1])
            extY = max(input_extent[3], source_extent[3])
            extZ = max(input_extent[5], source_extent[5])            
            padX = extX - source_extent[1]
            padY = extY - source_extent[3]
            padZ = extZ - source_extent[5]            
            print 'Zero-padding source by (%d, %d, %d) voxels to force extent to match/exceed input''s extent. Lame, eh?' % (padX, padY, padZ)            
            self._padder.SetInput(self._source)
            self._padder.SetConstant(0.0)
            self._padder.SetOutputWholeExtent(source_extent[0],extX,source_extent[2],extY,source_extent[4],extZ)
            self._padder.Update()
            self._source.DeepCopy(self._padder.GetOutput())
            
    def execute_module(self):
        if self._source.IsA('vtkImageData') and self._input.IsA('vtkImageData'):
            self.pad_source()          
    
        self._probeFilter.SetInput(self._input)
        self._probeFilter.SetSource(self._source)
        self._probeFilter.Update()