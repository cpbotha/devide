# class generated by DeVIDE::createDeVIDEModuleFromVTKObject
from module_kits.vtk_kit.mixins import SimpleVTKClassModuleBase
import vtk

class vtkBoxClipDataSet(SimpleVTKClassModuleBase):
    def __init__(self, module_manager):
        SimpleVTKClassModuleBase.__init__(
            self, module_manager,
            vtk.vtkBoxClipDataSet(), 'Processing.',
            ('vtkDataSet',), ('vtkUnstructuredGrid', 'vtkUnstructuredGrid'),
            replaceDoc=True,
            inputFunctions=None, outputFunctions=None)
