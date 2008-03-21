# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

def major_axis_from_iop_cosine(iop_cosine):
    """Given an IOP direction cosine, i.e. either the row or column,
    return a tuple with two components from LRPAFH signifying the
    direction of the cosine.  For example, if the cosine is pointing from
    Left to Right (1\0\0) we return ('L', 'R').

    If the direction cosine is NOT aligned with any of the major axes,
    we return None.

    Based on a routine from dclunie's pixelmed software and info from
    http://www.itk.org/pipermail/insight-users/2003-September/004762.html
    but we've flipped some things around to make more sense.

    IOP direction cosines are always in the RAH system:
     * x is left to right
     * y is posterior to anterior
     * z is foot to head <-- seems this might be the other way around,
       judging by dclunie's code.
    """

    obliquity_threshold = 0.8

    orientation_x = [('L', 'R'), ('R', 'L')][int(iop_cosine[0] > 0)]
    orientation_y = [('P', 'A'), ('A', 'P')][int(iop_cosine[1] > 0)]
    orientation_z = [('H', 'F'), ('F', 'H')][int(iop_cosine[2] > 0)]

    abs_x = abs(iop_cosine[0])
    abs_y = abs(iop_cosine[1])
    abs_z = abs(iop_cosine[2])

    if abs_x > obliquity_threshold and abs_x > abs_y and abs_x > abs_z:
        return orientation_x

    elif abs_y > obliquity_threshold and abs_y > abs_x and abs_y > abs_z:
        return orientation_y

    elif abs_z > obliquity_threshold and abs_z > abs_x and abs_z > abs_y:
        return orientation_z

    else:
        return None

