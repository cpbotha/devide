from moduleMixins import simpleVTKClassModuleBase
import vtk
import vtkdevide

class imageBorderMask(simpleVTKClassModuleBase):

    def __init__(self, moduleManager):
        simpleVTKClassModuleBase.__init__(
            self, moduleManager,
            vtkdevide.vtkImageBorderMask(), 'Creating border mask.',
            ('VTK Image Data',), ('Border Mask (vtkImageData)',))


                                          
