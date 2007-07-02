from moduleBase import moduleBase
from moduleMixins import introspectModuleMixin
import moduleUtils
import Measure2DFrame
reload(Measure2DFrame)

import vtk

class Measure2D(introspectModuleMixin, moduleBase):

    def __init__(self, module_manager):
        moduleBase.__init__(self, module_manager)

        self._view_frame = None
        self._viewer = None
        self._input_image = None
        
    def close(self):
        if self._view_frame is not None:
            self._view_frame.close()
            
    def view(self):
        if self._view_frame is None:
            self._view_frame = moduleUtils.instantiateModuleViewFrame(
                self, self._moduleManager, Measure2DFrame.Measure2DFrame)

            self._create_vtk_pipeline()
            
        self._view_frame.Show()
        
    def get_input_descriptions(self):
        return ('Image data',)

    def get_output_descriptions(self):
        return ()

    def execute_module(self):
        pass

    def logic_to_config(self):
        pass

    def config_to_logic(self):
        pass
    
    def set_input(self, idx, input_stream):
        self._input_image = input_stream
        self._setup_new_image()

    def _create_vtk_pipeline(self):
        """Create pipeline for viewing 2D image data.
        
        """
        if self._viewer is None and not self._view_frame is None:
            #self._ren = vtk.vtkRenderer()
            #self._ren.SetBackground(0.5,0.5,0.5)
            #self._view_frame._rwi.GetRenderWindow().AddRenderer(self._ren)
            
            #self._image_actor = vtk.vtkImageActor()
            #self._ren.AddViewProp(self._image_actor)
            
            # could be that input has already been set, but that view was
            # instantiated later.

            self._viewer = vtk.vtkImageViewer2()
            self._viewer.SetupInteractor(self._view_frame._rwi)
            
            
            if False:
                ss = vtk.vtkSphereSource()
                sm = vtk.vtkPolyDataMapper()
                sm.SetInput(ss.GetOutput())
                sa = vtk.vtkActor()
                sa.SetMapper(sm)
                self._ren.AddViewProp(sa)
                
    def _setup_new_image(self):
        """Based on the current self._input_image and the viewer, this thing will make sure
        that we reset to some usable default.
        """
        
        if not self._input_image is None and not self._viewer is None:
            self._viewer.SetInput(self._input_image)
            
            self._input_image.UpdateInformation()
            self._input_image.Update()
            range = self._input_image.GetScalarRange()
            self._viewer.SetColorWindow(range[1] - range[0])
            self._viewer.SetColorLevel(0.5 * (range[1] + range[0]))
            
            self._viewer.UpdateDisplayExtent()
            self._viewer.GetRenderer().ResetCamera()
            self._view_frame._rwi.Render()

            
