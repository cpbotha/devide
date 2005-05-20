# $Id: __init__.py,v 1.2 2005/05/20 12:12:37 cpbotha Exp $
# This should be functionally equivalent to InsightToolkit.py

# the sequence of library loads cause by the following two statements is:
# ITKCommon{A,B}Python, ITKBasicFilters{A,B}Python, ITKNumericsPython,
# ITKAlgorithmsPython, ITKIOPython

from itkAlgorithmsPythonTopLevel import *
from itkIOPythonTopLevel import *

