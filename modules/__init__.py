# __init__.py by Charl P. Botha <cpbotha@ieee.org>
# $Id: __init__.py,v 1.122 2005/06/10 23:13:39 cpbotha Exp $
# contains list of built-in modules; update when adding new modules
# the user_modules get listed automatically

# we HAVE to hard-code this list, because all these modules will be frozen
# along with the application... we can't search directories.

# module name is key, tuple with categories is value.  you can have any
# list of categories, they may also overlap

moduleList = {'Readers.dicomRDR' : ('Readers',),
              'Readers.objRDR' : ('Readers',),
              'Readers.metaImageRDR' : ('Readers',),
              'Readers.pngRDR' : ('Readers',),
              'Readers.rawVolumeRDR' : ('Readers',),
              'Readers.stlRDR' : ('Readers',),
              'Readers.vtiRDR' : ('Readers',),
              'Readers.vtpRDR' : ('Readers',),
              'Readers.vtkPolyDataRDR' : ('Readers',),
              'Readers.vtkStructPtsRDR' : ('Readers',),

              'Viewers.histogram1D' : ('Viewers',),
              'Viewers.histogram2D' : ('Viewers',),
              'Viewers.histogramSegment' : ('Viewers',),
              'Viewers.slice3dVWR' : ('Viewers',),

              'Filters.appendPolyData' : ('Filters',),
              'Filters.clipPolyData' : ('Filters',),
              'Filters.contour' : ('Filters',),
              'Filters.decimate' : ('Filters',),
              'Filters.doubleThreshold' : ('Filters',),
              'Filters.extractGrid' : ('Filters',),
              'Filters.extractHDomes' : ('Filters', 'Morphology'),
              'Filters.extractImageComponents' : ('Filters',),
              'Filters.glyphs' : ('Filters',),
              'Filters.greyReconstruct' : ('Filters', 'Morphology'),
              'Filters.imageFillHoles' : ('Filters', 'Morphology'),
              'Filters.imageFlip' : ('Filters',),
              'Filters.imageGaussianSmooth' : ('Filters',),
              'Filters.imageGreyDilate' : ('Filters', 'Morphology'),
              'Filters.imageGreyErode' : ('Filters', 'Morphology'),
              'Filters.imageGradientMagnitude' : ('Filters',),
              'Filters.imageMask' : ('Filters',),
              'Filters.imageMathematics' : ('Filters',),
              'Filters.imageMedian3D' : ('Filters',),
              #'Filters.isolatedConnect',
              'Filters.glenoidMouldDesign' : ('Filters',),
              'Filters.landmarkTransform' : ('Filters',),

              'Filters.marchingCubes' : ('Filters',),
              'Filters.modifyHomotopy' : ('Filters', 'Morphology'),
              'Filters.morphGradient' : ('Filters', 'Morphology'),
              'Filters.opening' : ('Filters', 'Morphology'),
              'Filters.probeFilter' : ('Filters',),
              'Filters.closing' : ('Filters', 'Morphology'),
              'Filters.polyDataConnect' : ('Filters',),
              'Filters.polyDataNormals' : ('Filters',),
              'Filters.resampleImage' : ('Filters',),
              'Filters.seedConnect' : ('Filters',),
              'Filters.selectConnectedComponents' : ('Filters',),
              'Filters.shellSplatSimple' : ('Filters',),
              'Filters.streamTracer' : ('Filters',),
              'Filters.surfaceToDistanceField' : ('Filters',),
              'Filters.transformPolyData' : ('Filters',),
              'Filters.transformVolumeData' : ('Filters',),
              'Filters.warpPoints' : ('Filters',),
              'Filters.wsMeshSmooth' : ('Filters',),

              'Writers.cptBrepWRT' : ('Writers',),
              'Writers.pngWRT' : ('Writers',),
              'Writers.ivWRT' : ('Writers',),
              'Writers.stlWRT' : ('Writers',),
              'Writers.vtiWRT' : ('Writers',),
              'Writers.vtpWRT' : ('Writers',),
              'Writers.vtkPolyDataWRT' : ('Writers',),
              'Writers.vtkStructPtsWRT' : ('Writers',),

              'Misc.advectionProperties' : ('Misc',),
              'Misc.cptDistanceField' : ('Misc',),
              'Misc.manualTransform' : ('Misc', 'Sources'),
              'Misc.pointsToSpheres' : ('Misc', 'Sources'),
              'Misc.superQuadric' : ('Sources',),
              'Misc.implicitToVolume' : ('Sources',),
              
              'ifdoc.ifdocRDR' : ('ifdoc',),
              'ifdoc.ifdocVWR' : ('ifdoc',),

              'Insight.curvatureFlowDenoising' : ('Insight',),
              'Insight.demonsRegistration' : ('Insight',),
              'Insight.distanceMap' : ('Insight',),
              'Insight.fastMarching' : ('Insight',),
              'Insight.gradientAnisotropicDiffusion' : ('Insight',),
              'Insight.gradientMagnitudeGaussian' : ('Insight',),
              'Insight.cannyEdgeDetection' : ('Insight',),
              'Insight.curvatureAnisotropicDiffusion' : ('Insight',),
              'Insight.gaussianConvolve' : ('Insight',),
              'Insight.geodesicActiveContour' : ('Insight', 'Level Sets'),

              # temporarily removed because it doesn't work on windows
              #'Insight.gvfgac' : ('Insight', 'Level Sets'),
              
              # temporarily removed because ITK has no wrapping for it!
              #'Insight.levelSetMotionRegistration' : ('Insight', 'Level Sets'),
              'Insight.nbCurvesLevelSet' : ('Insight',),
              'Insight.sigmoid' : ('Insight',),
              'Insight.symmetricDemonsRegistration' : ('Insight',),
              'Insight.watershed' : ('Insight', 'Morphology'),
              'Insight.imageStackRDR' : ('Insight',),
              'Insight.itk3RDR' : ('Insight', 'Readers'),
              'Insight.itkWRT' : ('Insight', 'Writers'),
              'Insight.confidenceSeedConnect' : ('Insight',),
              'Insight.discreteLaplacian' : ('Insight',),
              'Insight.nbhSeedConnect' : ('Insight',),
              'Insight.register2D' : ('Insight',),
              'Insight.tpgac' : ('Insight', 'Level Sets'),

              'Insight.transform2D' : ('Insight',),
              'Insight.transformStackWRT' : ('Insight',),
              'Insight.transformStackRDR' : ('Insight',),
              'Insight.VTKtoITKF3' : ('Insight',),
              'Insight.ITKF3toVTK' : ('Insight',),
              'Insight.ITKUL3toVTK' : ('Insight',),
              'Insight.ITKUS3toVTK' : ('Insight',)
              }




