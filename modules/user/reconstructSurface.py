from module_base import ModuleBase
from module_mixins import NoConfigModuleMixin
import module_utils
import vtk

class reconstructSurface(ModuleBase, NoConfigModuleMixin):
    """Given a binary volume, fit a surface through the marked points.

    A doubleThreshold could be used to extract points of interest from
    a volume.  By passing it through this module, a surface will be
    fit through those points of interest.  The points of interest have
    to be of value 1 or greater.

    This is not to be confused with traditional iso-surface extraction.
    """
    

    def __init__(self, module_manager):
        # initialise our base class
        ModuleBase.__init__(self, module_manager)
        # initialise any mixins we might have
        NoConfigModuleMixin.__init__(self)


        # we'll be playing around with some vtk objects, this could
        # be anything
        self._thresh = vtk.vtkThresholdPoints()
        # this is wacked syntax!
        self._thresh.ThresholdByUpper(1)
        self._reconstructionFilter = vtk.vtkSurfaceReconstructionFilter()
        self._reconstructionFilter.SetInput(self._thresh.GetOutput())
        self._mc = vtk.vtkMarchingCubes()
        self._mc.SetInput(self._reconstructionFilter.GetOutput())
        self._mc.SetValue(0, 0.0)

        module_utils.setupVTKObjectProgress(self, self._thresh,
                                           'Extracting points...')
        module_utils.setupVTKObjectProgress(self, self._reconstructionFilter,
                                           'Reconstructing...')
        module_utils.setupVTKObjectProgress(self, self._mc,
                                           'Extracting surface...')

        self._iObj = self._thresh
        self._oObj = self._mc
        
        self._viewFrame = self._createViewFrame({'threshold' :
                                                 self._thresh,
                                                 'reconstructionFilter' :
                                                 self._reconstructionFilter,
                                                 'marchingCubes' :
                                                 self._mc})


    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)
        # don't forget to call the close() method of the vtkPipeline mixin
        NoConfigModuleMixin.close(self)
        # get rid of our reference
        del self._thresh
        del self._reconstructionFilter
        del self._mc
        del self._iObj
        del self._oObj

    def get_input_descriptions(self):
	return ('vtkImageData',)

    def set_input(self, idx, inputStream):
        self._iObj.SetInput(inputStream)

    def get_output_descriptions(self):
        return (self._oObj.GetOutput().GetClassName(),)

    def get_output(self, idx):
        return self._oObj.GetOutput()

    def logic_to_config(self):
        pass

    def config_to_logic(self):
        pass

    def view_to_config(self):
        pass

    def config_to_view(self):
        pass

    def execute_module(self):
        self._oObj.Update()

    def view(self, parent_window=None):
        self._viewFrame.Show(True)
        self._viewFrame.Raise()
