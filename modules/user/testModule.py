from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import moduleUtils
import vtk

class testModule(noConfigModuleMixin, moduleBase):

    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)


        # we'll be playing around with some vtk objects, this could
        # be anything
        self._triangleFilter = vtk.vtkTriangleFilter()
        self._curvatures = vtk.vtkCurvatures()
        self._curvatures.SetCurvatureTypeToMaximum()
        self._curvatures.SetInput(self._triangleFilter.GetOutput())

        # initialise any mixins we might have
        noConfigModuleMixin.__init__(self,
                {'Module (self)' : self,
                    'vtkTriangleFilter' : self._triangleFilter,
                    'vtkCurvatures' : self._curvatures})

        moduleUtils.setupVTKObjectProgress(self, self._triangleFilter,
                                           'Triangle filtering...')
        moduleUtils.setupVTKObjectProgress(self, self._curvatures,
                                           'Calculating curvatures...')
        
        
        self.sync_module_logic_with_config()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)
        # don't forget to call the close() method of the vtkPipeline mixin
        noConfigModuleMixin.close(self)
        # get rid of our reference
        del self._triangleFilter
        del self._curvatures

    def get_input_descriptions(self):
        return ('vtkPolyData',)

    def set_input(self, idx, inputStream):
        self._triangleFilter.SetInput(inputStream)

    def get_output_descriptions(self):
        return (self._curvatures.GetOutput().GetClassName(),)

    def get_output(self, idx):
        return self._curvatures.GetOutput()

    def execute_module(self):
        self._curvatures.Update()

    def streaming_execute_module(self):
        self._curvatures.Update()


