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
        self._ren = None


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
        return ()

    def get_output_descriptions(self):
        return ()

    def execute(self):
        pass

    def logic_to_config(self):
        pass

    def config_to_logic(self):
        pass

    def _create_vtk_pipeline(self):
        if self._view_frame is not None and self._ren is None:
            self._ren = vtk.vtkRenderer()
            self._ren.SetBackground(0.5,0.5,0.5)
            self._view_frame._rwi.GetRenderWindow().AddRenderer(self._ren)

            ss = vtk.vtkSphereSource()
            sm = vtk.vtkPolyDataMapper()
            sm.SetInput(ss.GetOutput())
            sa = vtk.vtkActor()
            sa.SetMapper(sm)
            self._ren.AddViewProp(sa)
            
