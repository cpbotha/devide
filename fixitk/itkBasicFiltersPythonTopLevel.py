from itkCommonPythonTopLevel import *
__itk_import_data__ = itkBasePythonTopLevel.preimport()
from ITKBasicFiltersPython import *

# ITKBasicFiltersBPython was added AFTER ITK 1.6
try:
    from ITKBasicFiltersBPython import *
except ImportError:
    pass

itkBasePythonTopLevel.postimport(__itk_import_data__)
