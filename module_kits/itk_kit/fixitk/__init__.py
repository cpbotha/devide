# $Id$
# This should be functionally equivalent to InsightToolkit.py

# the sequence of library loads cause by the following two statements is:
# VXLNumericsPython
# ITKCommon{A,B}Python, ITKBasicFilters{A,B}Python, ITKNumericsPython,
# ITKAlgorithmsPython, ITKIOPython

from itkAlgorithmsPythonTopLevel import *
from itkIOPythonTopLevel import *

