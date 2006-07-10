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

class distanceMap:
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
    cats = ['Insight']

class gradientAnisotropicDiffusion:
    kits = ['itk_kit']
    cats = ['Insight']

# had to disable as ITK 2-4-1 has the standard moron-idiot executing without
# input crashes the whole of your application thank you very much bug
#class gradientMagnitudeGaussian:
#    kits = ['itk_kit']
#    cats = ['Insight']

# isn't wrapped anymore, no idea why.
#class gvfgac:
#    kits = ['itk_kit']
#    cats = ['Insight']

# will fix when I rework the registration modules
#class imageStackRDR:
#    kits = ['itk_kit']
#    cats = ['Insight']

#class isolatedConnect:
#    kits = ['itk_kit']
#    cats = ['Insight']

class itk3RDR:
    kits = ['itk_kit']
    cats = ['Insight', 'Readers']

class itkWRT:
    kits = ['itk_kit']
    cats = ['Insight', 'Writers']

# not wrapped by ITK-2-4-1 default wrappings
#class levelSetMotionRegistration:
#    kits = ['itk_kit']
#    cats = ['Insight']

class nbCurvesLevelSet:
    kits = ['itk_kit']
    cats = ['Insight']

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

class symmetricDemonsRegistration:
    kits = ['itk_kit']
    cats = ['Insight']

class tpgac:
    kits = ['itk_kit']
    cats = ['Insight']

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

