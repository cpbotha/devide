# class generated by DeVIDE::createDeVIDEModuleFromVTKObject
from module_kits.vtk_kit.mixins import SimpleVTKClassModuleBase
import vtk

class vtkExtractTemporalFieldData(SimpleVTKClassModuleBase):
    def __init__(self, module_manager):
        SimpleVTKClassModuleBase.__init__(
            self, module_manager,
            vtk.vtkExtractTemporalFieldData(), 'Processing.',
            ('vtkDataSet',), ('vtkRectilinearGrid',),
            replaceDoc=True,
            inputFunctions=None, outputFunctions=None)
