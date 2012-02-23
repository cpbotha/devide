# class generated by DeVIDE::createDeVIDEModuleFromVTKObject
from module_kits.vtk_kit.mixins import SimpleVTKClassModuleBase
import vtk

class vtkVertexDegree(SimpleVTKClassModuleBase):
    def __init__(self, module_manager):
        SimpleVTKClassModuleBase.__init__(
            self, module_manager,
            vtk.vtkVertexDegree(), 'Processing.',
            ('vtkAbstractGraph',), ('vtkAbstractGraph',),
            replaceDoc=True,
            inputFunctions=None, outputFunctions=None)
