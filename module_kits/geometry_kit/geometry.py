import math
import numpy

def normalise_line(p1, p2):
    """Given two points, return normal vector, magnitude and original
    line vector.

    Example: normal_vec, mag, line_vec = normalize_line(p1_tuple, p2_tuple)
    """

    line_vector = numpy.array(p2) - numpy.array(p1)

    squared_norm = numpy.sum(line_vector * line_vector)
    norm = numpy.sqrt(squared_norm)
    unit_vec = line_vector / norm

    return (unit_vec, norm, line_vector)

def dot(v1, v2):
    """Return dot-product between vectors v1 and v2.
    """

    dot_product = numpy.sum(numpy.array(v1) * numpy.array(v2))
    return dot_product

def move_line_to_target_along_normal(p1, p2, n, target):
    """Move the line (p1,p2) along normal vector n until it intersects 
    with target.

    @returns: Adjusted p1,p2
    """

    p1a = numpy.array(p1)
    p2a = numpy.array(p2)
    ta = numpy.array(target)

    # see how far p2a is from ta measured along n
    dp = dot(p2a - ta, n)

    # better to use an epsilon?
    if numpy.absolute(dp) > 0.0:
        # calculate vector needed to correct along n
        dvec = - dp * n
        p1a = p1a + dvec
        p2a = p2a + dvec

    return (p1a, p2a)


def intersect_line_sphere(p1, p2, sc, r):
    """Calculates intersection between line going through p1 and p2 and
    sphere determined by centre sc and radius r.

    Requires numpy.

    @param p1: tuple, or 1D matrix, or 1D array with first point defining line.
    @param p2: tuple, or 1D matrix, or 1D array with second point defining line.

    See http://local.wasp.uwa.edu.au/~pbourke/geometry/sphereline/source.cpp
    """

    # a is squared distance between the two points defining line
    p_diff = numpy.array(p2) - numpy.array(p1)
    a = numpy.sum(numpy.multiply(p_diff, p_diff))

    b = 2 * ( (p2[0] - p1[0]) * (p1[0] - sc[0]) + \
              (p2[1] - p1[1]) * (p1[1] - sc[1]) + \
              (p2[2] - p1[2]) * (p1[2] - sc[2]) )

    c = sc[0] ** 2 + sc[1] ** 2 + \
        sc[2] ** 2 + p1[0] ** 2 + \
        p1[1] ** 2 + p1[2] ** 2 - \
        2 * (sc[0] * p1[0] + sc[1] * p1[1] + sc[2]*p1[2]) - r ** 2

    i = b * b - 4 * a * c

    if (i < 0.0):
        # no intersections
        return []

    if (i == 0.0):
        # one intersection
        mu = -b / (2 * a)
        return [ (p1[0] + mu * (p2[0] - p1[0]),
                  p1[1] + mu * (p2[1] - p1[1]),
                  p1[2] + mu * (p2[2] - p1[2])) ]

    if (i > 0.0):
        # two intersections
        mu = (-b + math.sqrt( b ** 2 - 4*a*c )) / (2*a)
        i1 = (p1[0] + mu * (p2[0] - p1[0]),
              p1[1] + mu * (p2[1] - p1[1]),
              p1[2] + mu * (p2[2] - p1[2]))
                
        mu = (-b - math.sqrt( b ** 2 - 4*a*c )) / (2*a)
        i2 = (p1[0] + mu * (p2[0] - p1[0]),
              p1[1] + mu * (p2[1] - p1[1]),
              p1[2] + mu * (p2[2] - p1[2]))

        # in the case of two intersections, we want to make sure
        # that the vector i1,i2 has the same orientation as vector p1,p2
        i_diff = numpy.array(i2) - numpy.array(i1)
        if numpy.dot(p_diff, i_diff) < 0:
            return [i2, i1]
        else:
            return [i1, i2]

def intersect_line_ellipsoid(p1, p2, ec, radius_vectors):
    """Determine intersection points between line defined by p1 and p2,
    and ellipsoid defined by centre ec and three radius vectors (tuple
    of tuples, each inner tuple is a radius vector).

    This requires numpy.
    """


    # create transformation matrix that has the radius_vectors
    # as its columns (hence the transpose)
    rv = numpy.transpose(numpy.matrix(radius_vectors))
    # calculate its inverse
    rv_inv = numpy.linalg.pinv(rv)
    
    # now transform the two points
    # all points have to be relative to ellipsoid centre
    # the [0] at the end and the numpy.array at the start is to make sure
    # we pass a row vector (array) to the line_sphere_intersection
    p1_e = numpy.array(numpy.matrixmultiply(rv_inv, numpy.array(p1) - numpy.array(ec)))[0]
    p2_e = numpy.array(numpy.matrixmultiply(rv_inv, numpy.array(p2) - numpy.array(ec)))[0]

    # now we only have to determine the intersection between the points
    # (now transformed to ellipsoid space) with the unit sphere centred at 0
    isects_e = intersect_line_sphere(p1_e, p2_e, (0.0,0.0,0.0), 1.0)

    # transform intersections back to "normal" space
    isects = []
    for i in isects_e:
        # numpy.array(...)[0] is for returning only row of matrix as array
        itemp = numpy.array(numpy.matrixmultiply(rv, numpy.array(i)))[0]
        isects.append(itemp + numpy.array(ec))

    return isects

def intersect_line_mask(p1, p2, mask, incr):
    """Calculate FIRST intersection of line (p1,p2) with mask, as we walk
    from p1 to p2 with increments == incr.
    """

    p1 = numpy.array(p1)
    p2 = numpy.array(p2)

    origin = numpy.array(mask.GetOrigin())
    spacing = numpy.array(mask.GetSpacing())

    incr = float(incr)

    line_vector = p2 - p1
    squared_norm = numpy.sum(line_vector * line_vector)
    norm = numpy.sqrt(squared_norm)
    unit_vec = line_vector / norm

    curp = p1

    intersect = False
    end_of_line = False
    i_point = numpy.array((), float) # empty array
    
    while not intersect and not end_of_line:
        # get voxel coords
        voxc = (curp - origin) / spacing

        e = mask.GetExtent()
        if voxc[0] >= e[0] and voxc[0] <= e[1] and \
           voxc[1] >= e[2] and voxc[1] <= e[3] and \
           voxc[2] >= e[4] and voxc[2] <= e[5]:
            val = mask.GetScalarComponentAsDouble(
                voxc[0], voxc[1], voxc[2], 0)
        else:
            val = 0.0

        if val > 0.0:
            intersect = True
            i_point = curp
        else:    
            curp = curp + unit_vec * incr

        cur_squared_norm = numpy.sum(numpy.square(curp - p1))
        if  cur_squared_norm > squared_norm:
            end_of_line = True

    if end_of_line:
        return None
    else:
        return i_point

