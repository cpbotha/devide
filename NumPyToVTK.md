With the following code, you should be able to convert numpy arrays to VTK image data:
```
from vtk.util import numpy_support
vtkarray = numpy_support.numpy_to_vtk(numpy_array)
numpy_array2 = numpy_support.vtk_to_numpy(vtkarray)
```