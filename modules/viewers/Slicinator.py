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

from moduleBase import moduleBase
from moduleMixins import introspectModuleMixin
import moduleUtils

class Slicinator(IntrospectModuleMixin, moduleBase):
    pass

