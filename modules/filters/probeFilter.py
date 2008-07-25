import genUtils
from module_base import ModuleBase
from moduleMixins import noConfigModuleMixin
import moduleUtils
import vtk


class probeFilter(noConfigModuleMixin, ModuleBase):
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
        
        self._probeFilter = vtk.vtkProbeFilter()
        self._probeFilter.SetInput(self._dummyInput)

        noConfigModuleMixin.__init__(
            self,
            {'Module (self)' : self,
             'vtkProbeFilter' : self._probeFilter})

        moduleUtils.setupVTKObjectProgress(self, self._probeFilter,
                                           'Mapping source on input')
        
        self.sync_module_logic_with_config()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        noConfigModuleMixin.close(self)
        
        # get rid of our reference
        del self._probeFilter
        del self._dummyInput

    def get_input_descriptions(self):
        return ('Input', 'Source')

    def set_input(self, idx, inputStream):
        if idx == 0:
            if inputStream == None:
                # we don't really disconnect, we just reset the dummy
                # input...
                self._probeFilter.SetInput(self._dummyInput)
            else:
                self._probeFilter.SetInput(inputStream)

        else:
            self._probeFilter.SetSource(inputStream)

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
    
    def execute_module(self):
        self._probeFilter.Update()
