from moduleMixins import simpleVTKClassModuleBase
import vtk

class simplestVTKExample(simpleVTKClassModuleBase):
    """This is the minimum you need to wrap a single VTK object.

    Neat huh?
    """

    def __init__(self, moduleManager):
        simpleVTKClassModuleBase.__init__(
            self, moduleManager,
            vtk.vtkStripper(), 'Stripping polydata.',
            ('vtkPolyData',), ('Stripped vtkPolyData',))


                                          
