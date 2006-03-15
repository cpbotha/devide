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

class curvatureAnisotropicDiffusion:
    kits = ['itk_kit']
    cats = ['Insight']

class curvatureFlowDenoising:
    kits = ['itk_kit']
    cats = ['Insight']

class DanielssonDistance:
    kits = ['itk_kit']
    cats = ['Insight']

class demonsRegistration:
    kits = ['itk_kit']
    cats = ['Insight']

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

