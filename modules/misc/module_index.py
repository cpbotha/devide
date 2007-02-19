# $Id$

class advectionProperties:
    kits = ['vtk_kit']
    cats = ['Sources']
    help = """Given a series of prepared advection volumes (each input is a
    timestep), calculate a number of metrics.

    The first input HAS to have a VolumeIndex PointData attribute/array.  For
    example, the output of the pointsToSpheres that you used BEFORE having
    passed through the first probeFilters.  This first input will NOT be used
    for the actual calculations, but only for point -> volume lookups.
    Calculations will be performed for the second input and onwards.

    This module writes a CSV file with the volume centroids over time, and
    secretly writes a python file with all data as a python nested list.
    This can easily be loaded in a Python script for further analysis.
    """
    
class cptDistanceField:
    kits = ['vtk_kit']
    cats = ['Sources']
    help = """Driver module for Mauch's CPT code.

    This takes an image data and a mesh input.  The imagedata is only used
    to determine the bounds of the output distance field.  The mesh
    is converted to the CPT brep format using the DeVIDE cptBrepWRT module.
    A geom file is created.  The CPT driver is executed with the geom and
    brep files.  The output distance field is read, y-axis is flipped, and
    the whole shebang is made available at the output.

    The distance will be calculated up to _maxDistance.

    """

    
class implicitToVolume:
    kits = ['vtk_kit']
    cats = ['Sources']
    help = """Given an implicit function, this module will evaluate it over
    a volume and yield that volume as output.
    """

class manualTransform:
    kits = ['vtk_kit']
    cats = ['Sources']
    help = """Manually create linear transform by entering scale factors,
    rotation angles and translations.

    Scaling is performed, then rotation, then translation.  It is often easier
    to chain manualTransform modules than performing all transformations at
    once.

    """


class pointsToSpheres:
    kits = ['vtk_kit']
    cats = ['Sources']
    help = """Given a set of selected points (for instance from a slice3dVWR),
    generate polydata spheres centred at these points with user-specified
    radius.  The spheres' interiors are filled with smaller spheres.  This is
    useful when using selected points to generate points for seeding
    streamlines or calculating advection by a vector field.

    Each point's sphere has an array associated to its pointdata called
    'VolumeIndex'.  All values in this array are equal to the corresponding
    point's index in the input points list.
    """


class superQuadric:
    kits = ['vtk_kit']
    cats = ['Sources']
    help = """Generates a SuperQuadric implicit function and polydata as
    outputs.
    """


