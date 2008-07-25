from moduleMixins import simpleVTKClassModuleBase
import vtktud

class imageKnutssonMapping(simpleVTKClassModuleBase):
    """This is the minimum you need to wrap a single VTK object.  This
    __doc__ string will be replaced by the __doc__ string of the encapsulated
    VTK object, i.e. vtkStripper in this case.

    With these few lines, we have error handling, progress reporting, module
    help and also: the complete state of the underlying VTK object is also
    pickled, i.e. when you save and restore a network, any changes you've
    made to the vtkObject will be restored.
    """

    def __init__(self, module_manager):
        simpleVTKClassModuleBase.__init__(
            self, module_manager,
            vtktud.vtkImageKnutssonMapping(), 'Image Knutsson Mapping.',
            ('vtkImageData',), ('vtkImageData',))
