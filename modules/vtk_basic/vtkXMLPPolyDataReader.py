# class generated by DeVIDE::createDeVIDEModuleFromVTKObject
from module_kits.vtk_kit.mixins import SimpleVTKClassModuleBase
import vtk

class vtkXMLPPolyDataReader(SimpleVTKClassModuleBase):
    def __init__(self, moduleManager):
        SimpleVTKClassModuleBase.__init__(
            self, moduleManager,
            vtk.vtkXMLPPolyDataReader(), 'Reading vtkXMLPPolyData.',
            (), ('vtkXMLPPolyData',),
            replaceDoc=True,
            inputFunctions=None, outputFunctions=None)