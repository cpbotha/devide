# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

# general requirements:
# * multiple objects (i.e. multiple coloured contours per slice)

# slice segmentation modes:
# * polygon mode
# * freehand drawing
# * 2d levelset

# see design notes on p39 of AM2 moleskine

from module_base import ModuleBase
from moduleMixins import introspectModuleMixin
import moduleUtils

class Slicinator(IntrospectModuleMixin, ModuleBase):
    pass

