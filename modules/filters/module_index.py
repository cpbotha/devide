# $Id$

# this one was generated with:
# for i in *.py; do n=`echo $i | cut -f 1 -d .`; \
# echo -e "class $n:\n    kits = ['vtk_kit']\n    cats = ['Filters']\n" \
# >> blaat.txt; done

class appendPolyData:
    kits = ['vtk_kit']
    cats = ['Filters']
    help = """DeVIDE encapsulation of the vtkAppendPolyDataFilter that
    enables us to combine multiple PolyData structures into one.

    DANGER WILL ROBINSON: contact the author, this module is BROKEN.
    """

class clipPolyData:
    kits = ['vtk_kit']
    cats = ['Filters']
    keywords = ['polydata', 'clip', 'implicit']
    help = \
         """Given an input polydata and an implicitFunction, this will clip
         the polydata.

         All points that are inside the implicit function are kept, everything
         else is discarded.  'Inside' is defined as all points in the polydata
         where the implicit function value is greater than 0.
         """

class closing:
    kits = ['vtk_kit']
    cats = ['Filters', 'Morphology']
    keywords = ['morphology']
    help = """Performs a greyscale morphological closing on the input image.

    Dilation is followed by erosion.  The structuring element is ellipsoidal
    with user specified sizes in 3 dimensions.  Specifying a size of 1 in any
    dimension will disable processing in that dimension.
    """

class contour:
    kits = ['vtk_kit']
    cats = ['Filters']
    help = """Extract isosurface from volume data.
    """

class decimate:
    kits = ['vtk_kit']
    cats = ['Filters']
    help = """Reduce number of triangles in surface mesh by merging triangles
    in areas of low detail.
    """

class doubleThreshold:
    kits = ['vtk_kit']
    cats = ['Filters']
    help = """Apply a lower and an upper threshold to the input image data.
    """

class extractGrid:
    kits = ['vtk_kit']
    cats = ['Filters']
    help = """Subsamples input dataset.

    This module makes use of the ParaView vtkPVExtractVOI class, which can
    handle structured points, structured grids and rectilinear grids.

    """

class extractHDomes:
    kits = ['vtk_kit']
    cats = ['Filters', 'Morphology']
    keywords = ['morphology']
    help = """Extracts light structures, also known as h-domes.

    The user specifies the parameter 'h' that indicates how much brighter the
    light structures are than their surroundings.  In short, this algorithm
    performs a fast greyscale reconstruction of the input image from a marker
    that is the image - h.  The result of this reconstruction is subtracted
    from the image.

    See 'Morphological Grayscale Reconstruction in Image Analysis:
    Applications and Efficient Algorithms', Luc Vincent, IEEE Trans. on Image
    Processing, 1993.

    """


class extractImageComponents:
    kits = ['vtk_kit']
    cats = ['Filters']
    help = """Extracts one, two or three components from multi-component
    image data.

    Specify the indices of the components you wish to extract and the number
    of components.
    """

class FitEllipsoidToMask:
    kits = ['numpy_kit', 'vtk_kit']
    cats = ['Filters']
    keywords = ['PCA', 'eigen-analysis', 'principal components', 'ellipsoid']
    help = """Given an image mask in VTK image data format, perform eigen-
    analysis on the world coordinates of 'on' points.

    Returns dictionary with eigen values in 'u', eigen vectors in 'v' and
    world coordinates centroid of 'on' points.
    """

class glyphs:
    kits = ['vtk_kit']
    cats = ['Filters']
    help = """Visualise vector field with glyphs.
    """

class greyReconstruct:
    kits = ['vtk_kit']
    cats = ['Filters', 'Morphology']
    keywords = ['morphology']
    help = """Performs grey value reconstruction of mask I from marker J.

    Theoretically, marker J is dilated and the infimum with mask I is
    determined.  This infimum now takes the place of J.  This process is
    repeated until stability.

    This module uses a DeVIDE specific implementation of Luc Vincent's fast
    hybrid algorithm for greyscale reconstruction.

    """

class imageFillHoles:
    kits = ['vtk_kit']
    cats = ['Filters', 'Morphology']
    keywords = ['morphology']
    help = """Filter to fill holes.

    In binary images, holes are image regions with 0-value that are completely
    surrounded by regions of 1-value.  This module can be used to fill these
    holes.  This filling also works on greyscale images.

    In addition, the definition of a hole can be adapted by 'deactivating'
    image borders so that 0-value regions that touch these deactivated borders
    are still considered to be holes and will be filled. 

    This module is based on two DeVIDE-specific filters: a fast greyscale
    reconstruction filter as per Luc Vincent and a special image border mask
    generator filter.
    """


class imageFlip:
    kits = ['vtk_kit']
    cats = ['Filters']
    help = """Flips image (volume) with regards to a single axis.

    At the moment, this flips by default about Z.  You can change this by
    introspecting and calling the SetFilteredAxis() method via the
    object inspection.
    """

class imageGaussianSmooth:
    kits = ['vtk_kit']
    cats = ['Filters']
    help = """Performs 3D Gaussian filtering of the input volume.
    """

class imageGradientMagnitude:
    kits = ['vtk_kit']
    cats = ['Filters']
    help = """Calculates the gradient magnitude of the input volume using
    central differences.
    """

class imageGreyDilate:
    kits = ['vtk_kit']
    cats = ['Filters', 'Morphology']
    keywords = ['morphology']
    help = """Performs a greyscale 3D dilation on the input.
    """

class imageGreyErode:
    kits = ['vtk_kit']
    cats = ['Filters', 'Morphology']
    keywords = ['morphology']
    help = """Performs a greyscale 3D erosion on the input.
    """

class ImageLogic:
    kits = ['vtk_kit']
    cats = ['Filters', 'Combine']
    help = """Performs pointwise boolean logic operations on input images.

    WARNING: vtkImageLogic in VTK 5.0 has a bug where it does require two
    inputs even if performing a NOT or a NOP.  This has been fixed in VTK CVS.
    DeVIDE will upgrade to > 5.0 as soon as a new stable VTK is released.
    
    """

class imageMask:
    kits = ['vtk_kit']
    cats = ['Filters', 'Combine']
    help = """The input data (input 1) is masked with the mask (input 2).

    The output image is identical to the input image wherever the mask has
    a value.  The output image is 0 everywhere else.
    """

class imageMathematics:
    kits = ['vtk_kit']
    cats = ['Filters', 'Combine']
    help = """Performs point-wise mathematical operations on one or two images.

    The underlying logic can do far more than the UI shows at this moment.
    Please let me know if you require more options.
    """

class imageMedian3D:
    kits = ['vtk_kit']
    cats = ['Filters', 'Morphology']
    keywords = ['morphology']
    help = """Performs 3D morphological median on input data.
    """

class landmarkTransform:
    kits = ['vtk_kit']
    cats = ['Filters']
    help = """The landmarkTransform will calculate a 4x4 linear transform
    that maps from a set of source landmarks to a set of target landmarks.

    The mapping is optimised with a least-squares metric.  You have to supply
    two sets of points, all points names in the source set have to start with
    'Source' and all the points names in the target set have to start with
    'Target'.

    This module will supply a vtkTransform at its output.  By
    connecting the vtkTransform to a transformPolyData module, you'll
    be able to perform the actual transformation.

    See the "Performing landmark registration on two volumes" example in the
    "Useful Patterns" section of the DeVIDE F1 central help.
    """

class marchingCubes:
    kits = ['vtk_kit']
    cats = ['Filters']
    help = """Extract surface from input volume using the Marching Cubes
    algorithm.
    """

class modifyHomotopy:
    kits = ['vtk_kit']
    cats = ['Filters', 'Morphology']
    keywords = ['morphology']
    help = """IMPORTANT: this module needs to be updated to the new
    event-driven execution scheme.  It should still work, but it may also
    blow up your computer.

    Modifies homotopy of input image I so that the only minima will
    be at the user-specified seed-points or marker image, all other
    minima will be suppressed and ridge lines separating minima will
    be preserved.

    Either the seed-points or the marker image (or both) can be used.
    The marker image has to be >1 at the minima that are to be enforced
    and 0 otherwise.

    This module is often used as a pre-processing step to ensure that
    the watershed doesn't over-segment.

    This module uses a DeVIDE-specific implementation of Luc Vincent's
    fast greyscale reconstruction algorithm, extended for 3D.
    
    """

class morphGradient:
    kits = ['vtk_kit']
    cats = ['Filters', 'Morphology']
    keywords = ['morphology']
    help = """Performs a greyscale morphological gradient on the input image.

    This is done by performing an erosion and a dilation of the input image
    and then subtracting the erosion from the dilation.  The structuring
    element is ellipsoidal with user specified sizes in 3 dimensions.
    Specifying a size of 1 in any dimension will disable processing in that
    dimension.

    This module can also return both half gradients: the inner (image -
    erosion) and the outer (dilation - image).
    """

class opening:
    kits = ['vtk_kit']
    cats = ['Filters', 'Morphology']
    keywords = ['morphology']
    help = """Performs a greyscale morphological opening on the input image.

    Erosion is followed by dilation.  The structuring element is ellipsoidal
    with user specified sizes in 3 dimensions.  Specifying a size of 1 in any
    dimension will disable processing in that dimension.
    """

class MIPRender:
    kits = ['vtk_kit']
    cats = ['Volume Rendering']
    help = """Performs Maximum Intensity Projection on the input volume /
    image.
    """

class polyDataConnect:
    kits = ['vtk_kit']
    cats = ['Filters']
    help = """Given a number of seed points, extract all polydata that is
    directly or indirectly connected to those seed points.  You could see
    this as a polydata-based region growing.
    """

class polyDataNormals:
    kits = ['vtk_kit']
    cats = ['Filters']
    help = """Calculate surface normals for input data mesh.
    """

class probeFilter:
    kits = ['vtk_kit']
    cats = ['Filters']
    help = """Maps source values onto input dataset.

    Input can be e.g. polydata and source a volume, in which case interpolated
    values from the volume will be mapped on the vertices of the polydata,
    i.e. the interpolated values will be associated as the attributes of the
    polydata points.

    """

class RegionGrowing:
    kits = ['vtk_kit']
    cats = ['Filters']
    help = """TBD"""

class resampleImage:
    kits = ['vtk_kit']
    cats = ['Filters']
    help = """Resample an image using nearest neighbour, linear or cubic
    interpolation.
    """

class seedConnect:
    kits = ['vtk_kit']
    cats = ['Filters']
    help = """3D region growing.

    Finds all points connected to the seed points that also have values
    equal to the 'Input Connected Value'.  This module casts all input to
    unsigned char.  The output is also unsigned char.
    """

class selectConnectedComponents:
    kits = ['vtk_kit']
    cats = ['Filters']
    help = """3D region growing.

    Finds all points connected to the seed points that have the same values
    as at the seed points.  This is primarily useful for selecting connected
    components.
    """

class shellSplatSimple:
    kits = ['vtk_kit']
    cats = ['Volume Rendering']
    help = """Simple configuration for ShellSplatting an input volume.

    ShellSplatting is a fast direct volume rendering method.  See
    http://visualisation.tudelft.nl/Projects/ShellSplatting for more
    information.
    """

class streamTracer:
    kits = ['vtk_kit']
    cats = ['Filters']
    help = """Visualise a vector field with stream lines.
    """

class surfaceToDistanceField:
    kits = ['vtk_kit']
    cats = ['Filters']
    help = """Given an input surface (vtkPolyData), create an unsigned
    distance field with the surface at distance 0.

    The user must specify the dimensions and bounds of the output volume.

    WARNING: this filter is *incredibly* slow, even for small volumes and
    extremely simple geometry.  Only use this if you know exactly what
    you're doing.
    """

class transformPolyData:
    kits = ['vtk_kit']
    cats = ['Filters']
    help = """Given a transform, for example the output of the
    landMarkTransform, this module will transform its input polydata.
    """


class transformVolumeData:
    kits = ['vtk_kit']
    cats = ['Filters']
    help = """Transform volume according to 4x4 homogeneous transform.
    """

class VolumeRender:
    kits = ['vtk_kit']
    cats = ['Volume Rendering']
    help = """Use direct volume rendering to visualise input volume.

    You can select between traditional raycasting, 2D texturing and 3D
    texturing.  The raycaster can only handler unsigned short or unsigned char
    data, so you might have to use a vtkShiftScale module to preprocess.

    You can supply your own opacity and colour transfer functions at the
    second and third inputs.  If you don't supply these, the module will
    create opacity and/or colour ramps based on the supplied threshold.
    """

class warpPoints:
    kits = ['vtk_kit']
    cats = ['Filters']
    help = """Warp input points according to their associated vectors.

    After connecting this module up, you have to execute the network, then
    click on the 'Sync' button to update the Vectors Selection drop down
    list.  At this point, you can select the correct input array, and
    'Apply'.  This input array is the one that will be used to warp the input.
    """

class wsMeshSmooth:
    kits = ['vtk_kit']
    cats = ['Filters']
    help = """Module that runs vtkWindowedSincPolyDataFilter on its input data
    for mesh smoothing.
    """
