from moduleMixins import simpleVTKClassModuleBase
import vtk

class simplestVTKExample(simpleVTKClassModuleBase):
    """This is the minimum you need to wrap a single VTK object.
    """

    def __init__(self, moduleManager):
        theThing = vtk.vtkStripper()
        simpleVTKClassModuleBase.__init__(self, moduleManager,
                                          theThing, 'Stripping stuff.')

    def getInputDescriptions(self):
        return ('vtkPolyData',)

    def getOutputDescriptions(self):
        return ('Stripped vtkPolyData',)

                                          
