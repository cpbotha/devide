# class generated by DeVIDE::createDeVIDEModuleFromVTKObject
from module_kits.vtk_kit.mixins import SimpleVTKClassModuleBase
import vtk

class vtkBMPReader(SimpleVTKClassModuleBase):
    def __init__(self, moduleManager):
        SimpleVTKClassModuleBase.__init__(
            self, moduleManager,
            vtk.vtkBMPReader(), 'Reading vtkBMP.',
            (), ('vtkBMP',),
            replaceDoc=True,
            inputFunctions=None, outputFunctions=None)