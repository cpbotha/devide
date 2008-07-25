# class generated by DeVIDE::createDeVIDEModuleFromVTKObject
from module_kits.vtk_kit.mixins import SimpleVTKClassModuleBase
import vtk

class vtkGlyph2D(SimpleVTKClassModuleBase):
    def __init__(self, module_manager):
        SimpleVTKClassModuleBase.__init__(
            self, module_manager,
            vtk.vtkGlyph2D(), 'Processing.',
            ('vtkDataSet', 'vtkPolyData'), ('vtkPolyData',),
            replaceDoc=True,
            inputFunctions=None, outputFunctions=None)
