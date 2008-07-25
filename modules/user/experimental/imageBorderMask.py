from moduleMixins import simpleVTKClassModuleBase
import vtk
import vtkdevide

class imageBorderMask(simpleVTKClassModuleBase):

    def __init__(self, module_manager):
        simpleVTKClassModuleBase.__init__(
            self, module_manager,
            vtkdevide.vtkImageBorderMask(), 'Creating border mask.',
            ('VTK Image Data',), ('Border Mask (vtkImageData)',))


                                          
