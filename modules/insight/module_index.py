# $Id$

class ITKF3toVTK:
    kits = ['itk_kit']
    cats = ['Insight']

class ITKUL3toVTK:
    kits = ['itk_kit']
    cats = ['Insight']

class ITKUS3toVTK:
    kits = ['itk_kit']
    cats = ['Insight']

class VTKtoITKF3:
    kits = ['itk_kit']
    cats = ['Insight']

class cannyEdgeDetection:
    kits = ['itk_kit']
    cats = ['Insight']

class confidenceSeedConnect:
    kits = ['itk_kit']
    cats = ['Insight']
    keywords = ['region growing', 'confidence', 'seed']
    help = """Confidence-based 3D region growing.

    This module will perform a 3D region growing starting from the
    user-supplied points.  The mean and standard deviation are calculated in a
    small initial region around the seed points.  New contiguous points have
    to have intensities on the range [mean - f*stdDev, mean + f*stdDev] to be
    included.  f is user-definable.

    After this initial growing iteration, if the user has specified a larger
    than 0 number of iterations, the mean and standard deviation are
    recalculated over all the currently selected points and the process is
    restarted.  This process is repeated for the user-defined number of
    iterations, or until now new pixels are added.

    Due to weirdness in the underlying ITK filter, deleting all points
    won't quite work.  In other words, the output of this module can
    only be trusted if there's at least a single seed point.
    """

class curvatureAnisotropicDiffusion:
    kits = ['itk_kit']
    cats = ['Insight']

class curvatureFlowDenoising:
    kits = ['itk_kit']
    cats = ['Insight']
    help = """Curvature-driven image denoising.

    This uses curvature-based level set techniques to smooth
    homogeneous regions whilst retaining boundary information.
    """


class DanielssonDistance:
    kits = ['itk_kit']
    cats = ['Insight']
    help = """Calculates distance image of input image.

    The input image can either contain marked objects or binary objects.
    """

class demonsRegistration:
    kits = ['itk_kit']
    cats = ['Insight']
    help = """Performs demons registration on fixed and moving input images,
    returns deformation field.
    
    The intensity difference threshold is absolute, so check the values in 
    your datasets and adjust it accordingly.  For example, if you find that
    two regions should match but you see intensity differences of 50 (e.g. 
    in a CT dataset), the threshold should be approximately 60.

    NOTE: remember to update help w.r.t. inverse direction of vectors in
    deformation field.

    Also read this thread:
    http://public.kitware.com/pipermail/insight-users/2004-November/011002.html
    """


class discreteLaplacian:
    kits = ['itk_kit']
    cats = ['Insight']

# had to disable this one due to stupid itkLevelSetNode non-wrapping
# in ITK-2-4-1
#class fastMarching:
#    kits = ['itk_kit']
#    cats = ['Insight']

class gaussianConvolve:
    kits = ['itk_kit']
    cats = ['Insight']

class geodesicActiveContour:
    kits = ['itk_kit']
    cats = ['Insight', 'Level Set']
    keywords = ['level set']
    help = """Module for performing Geodesic Active Contour-based segmentation
    on 3D data.

    The input feature image is an edge potential map with values close to 0 in
    regions close to the edges and values close to 1 otherwise.  The level set
    speed function is based on this.  For example: smooth an input image,
    determine the gradient magnitude and then pass it through a sigmoid
    transformation to create an edge potential map.

    The initial level set is a volume with the initial surface embedded as the
    0 level set, i.e. the 0-value iso-contour (more or less).

    Also see figure 9.18 in the ITK Software Guide.
    """


class gradientAnisotropicDiffusion:
    kits = ['itk_kit']
    cats = ['Insight']

# had to disable as ITK 2-4-1 has the standard moron-idiot executing without
# input crashes the whole of your application thank you very much bug
class gradientMagnitudeGaussian:
    kits = ['itk_kit']
    cats = ['Insight']
    help =  """Calculates gradient magnitude of an image by convolving with the
    derivative of a Gaussian.
    """

# isn't wrapped anymore, no idea why.
#class gvfgac:
#    kits = ['itk_kit']
#    cats = ['Insight']

# will fix when I rework the registration modules
#class imageStackRDR:
#    kits = ['itk_kit']
#    cats = ['Insight']

class isolatedConnect:
    kits = ['itk_kit']
    cats = ['Insight']
    keywords = ['segment']
    help = """Voxels connected to the first group of seeds and NOT connected
    to the second group of seeds are segmented by optimising an upper or
    lower threshold.

    For example, to separate two non-touching light objects, you would do the
    following:
    <ul>
    <li>Select point(s) in the first object with slice3dVWR 1</li>
    <li>Select point(s) in the second object with slice3dVWR 2</li>
    <li>Connect up the three inputs of isolatedConnect as follows: input
    image, point(s) of object 1, point(s) of object 2</li>
    <li>isolatedConnect will now calculate a threshold so that when this
    threshold is applied to the image and a region growing is performed using
    the first set of points, only object 1 will be separated.</li>
    </il>
    </ul>
    """

class ITKReader:
    kits = ['itk_kit']
    cats = ['Insight', 'Readers']
    help = """Reads all the 3D formats supported by ITK.  In its default
    configuration, this module will derive file type, data type and
    dimensionality from the file itself.  You can manually set the data type
    and dimensionality, in which case ITK will attempt to cast the data.

    Keep in mind that DeVIDE mostly uses the float versions of ITK components.

    At least the following file formats are available (a choice is made based
    on the filename extension that you choose):<br>
    <ul>
    <li>.mha: MetaImage all-in-one file</li>
    <li>.mhd: MetaImage .mhd header file and .raw data file</li>
    <li>.hdr or .img: Analyze .hdr header and .img data</li>
    </ul>

    """



class ITKWriter:
    kits = ['itk_kit']
    cats = ['Insight', 'Writers']
    help = """Writes any of the image formats supported by ITK.

    At least the following file formats are available (a choice is made based
    on the filename extension that you choose):<br>
    <ul>
    <li>.mha: MetaImage all-in-one file</li>
    <li>.mhd: MetaImage .mhd header file and .raw data file</li>
    <li>.hdr or .img: Analyze .hdr header and .img data</li>
    </ul>

    """

# not wrapped by ITK-2-4-1 default wrappings
class levelSetMotionRegistration:
    kits = ['itk_kit']
    cats = ['Insight', 'Registration']
    keywords = ['level set', 'registration', 'deformable', 'non-rigid']
    help = """Performs deformable registration between two input volumes using
    level set motion.
    """

# not wrapped by WrapITK 20060710
# class nbCurvesLevelSet:
#     kits = ['itk_kit']
#     cats = ['Insight', 'Level Set']
#     keywords = ['level set']
#     help = """Narrow band level set implementation.

#     The input feature image is an edge potential map with values close to 0 in
#     regions close to the edges and values close to 1 otherwise.  The level set
#     speed function is based on this.  For example: smooth an input image,
#     determine the gradient magnitude and then pass it through a sigmoid
#     transformation to create an edge potential map.

#     The initial level set is a volume with the initial surface embedded as the
#     0 level set, i.e. the 0-value iso-contour (more or less).
#     """

class nbhSeedConnect:
    kits = ['itk_kit']
    cats = ['Insight']

# reactivate when I rework the registration modules
#class register2D:
#    kits = ['itk_kit']
#    cats = ['Insight']

class sigmoid:
    kits = ['itk_kit']
    cats = ['Insight']
    help = """Perform sigmoid transformation on all input voxels.

    f(x) = (max - min) frac{1}{1 + exp(- frac{x - beta}{alpha})} + min
    """

class symmetricDemonsRegistration:
    kits = ['itk_kit']
    cats = ['Insight']
    help = """Performs symmetric forces demons registration on fixed and
    moving input images, returns deformation field.
    """

class tpgac:
    kits = ['itk_kit']
    cats = ['Insight', 'Level Sets']
    keywords = ['segment', 'level set']
    help = """Module for performing topology-preserving Geodesic Active
    Contour-based segmentation on 3D data.

    This module requires a DeVIDE-specific ITK class.

    The input feature image is an edge potential map with values close to 0 in
    regions close to the edges and values close to 1 otherwise.  The level set
    speed function is based on this.  For example: smooth an input image,
    determine the gradient magnitude and then pass it through a sigmoid
    transformation to create an edge potential map.

    The initial level set is a volume with the initial surface embedded as the
    0 level set, i.e. the 0-value iso-contour (more or less).

    Also see figure 9.18 in the ITK Software Guide.
    """


# will work on this when I rework the 2D registration
#class transform2D:
#    kits = ['itk_kit']
#    cats = ['Insight']

#class transformStackRDR:
#    kits = ['itk_kit']
#    cats = ['Insight']

#class transformStackWRT:
#    kits = ['itk_kit']
#    cats = ['Insight']

class watershed:
    kits = ['itk_kit']
    cats = ['Insight']
    help = """Perform watershed segmentation on input.

    Typically, the input will be the gradient magnitude image.  Often, data
    is smoothed with one of the anisotropic diffusion filters and then the
    gradient magnitude image is calculated.  This serves as input to the
    watershed module.
    """


