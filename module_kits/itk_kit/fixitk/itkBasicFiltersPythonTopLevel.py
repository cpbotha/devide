from itkCommonPythonTopLevel import *
__itk_import_data__ = itkBasePythonTopLevel.preimport()

# ITKBasicFiltersBPython was added AFTER ITK 1.6
try:
    from ITKBasicFiltersAPython import *
    from ITKBasicFiltersBPython import *
except ImportError:
    # we revert to old behaviour if the above libs can't be found
    from ITKBasicFiltersPython import *

itkBasePythonTopLevel.postimport(__itk_import_data__)
