# class generated by DeVIDE::createDeVIDEModuleFromVTKObject
from module_kits.vtk_kit.mixins import SimpleVTKClassModuleBase
import vtk

class vtkWin32VideoSource(SimpleVTKClassModuleBase):
    def __init__(self, module_manager):
        SimpleVTKClassModuleBase.__init__(
            self, module_manager,
            vtk.vtkWin32VideoSource(), 'Processing.',
            (), ('vtkImageData',),
            replaceDoc=True,
            inputFunctions=None, outputFunctions=None)
