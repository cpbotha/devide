# class generated by DeVIDE::createDeVIDEModuleFromVTKObject
from module_kits.vtk_kit.mixins import SimpleVTKClassModuleBase
import vtk

class vtkAttributeDataToFieldDataFilter(SimpleVTKClassModuleBase):
    def __init__(self, module_manager):
        SimpleVTKClassModuleBase.__init__(
            self, module_manager,
            vtk.vtkAttributeDataToFieldDataFilter(), 'Processing.',
            ('vtkDataSet',), ('vtkDataSet',),
            replaceDoc=True,
            inputFunctions=None, outputFunctions=None)
