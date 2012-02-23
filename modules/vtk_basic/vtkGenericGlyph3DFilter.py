# class generated by DeVIDE::createDeVIDEModuleFromVTKObject
from module_kits.vtk_kit.mixins import SimpleVTKClassModuleBase
import vtk

class vtkGenericGlyph3DFilter(SimpleVTKClassModuleBase):
    def __init__(self, module_manager):
        SimpleVTKClassModuleBase.__init__(
            self, module_manager,
            vtk.vtkGenericGlyph3DFilter(), 'Processing.',
            ('vtkGenericDataSet', 'vtkPolyData'), ('vtkPolyData',),
            replaceDoc=True,
            inputFunctions=None, outputFunctions=None)
