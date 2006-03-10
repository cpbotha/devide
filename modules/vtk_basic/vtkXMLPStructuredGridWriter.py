# class generated by DeVIDE::createDeVIDEModuleFromVTKObject
from module_kits.vtk_kit.mixins import SimpleVTKClassModuleBase
import vtk

class vtkXMLPStructuredGridWriter(SimpleVTKClassModuleBase):
    def __init__(self, moduleManager):
        SimpleVTKClassModuleBase.__init__(
            self, moduleManager,
            vtk.vtkXMLPStructuredGridWriter(), 'Writing vtkXMLPStructuredGrid.',
            ('vtkXMLPStructuredGrid',), (),
            replaceDoc=True,
            inputFunctions=None, outputFunctions=None)