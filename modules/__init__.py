# __init__.py by Charl P. Botha <cpbotha@ieee.org>
# $Id: __init__.py,v 1.73 2004/03/07 16:07:58 cpbotha Exp $
# contains list of built-in modules; update when adding new modules
# the user_modules get listed automatically

# we HAVE to hard-code this list, because all these modules will be frozen
# along with the application... we can't search directories.

# module name is key, tuple with categories is value.  you can have any
# list of categories, they may also overlap

moduleList = {'Readers.dicomRDR' : ('Readers',),
              'Readers.objRDR' : ('Readers',),
              'Readers.rawVolumeRDR' : ('Readers',),
              'Readers.stlRDR' : ('Readers',),
              'Readers.vtiRDR' : ('Readers',),
              'Readers.vtpRDR' : ('Readers',),
              'Readers.vtkPolyDataRDR' : ('Readers',),
              'Readers.vtkStructPtsRDR' : ('Readers',),

              'Viewers.histogram2D' : ('Viewers',),
              'Viewers.slice3dVWR' : ('Viewers',),

              'Filters.appendPolyData' : ('Filters',),
              'Filters.clipPolyData' : ('Filters',),
              'Filters.contour' : ('Filters',),
              'Filters.decimate' : ('Filters',),
              'Filters.doubleThreshold' : ('Filters',),
              'Filters.imageFlip' : ('Filters',),
              'Filters.imageGaussianSmooth' : ('Filters',),
              'Filters.imageGreyDilate' : ('Filters',),
              'Filters.imageGreyErode' : ('Filters',),
              'Filters.imageGradientMagnitude' : ('Filters',),
              'Filters.imageMask' : ('Filters',),
              'Filters.imageMedian3D' : ('Filters',),
              #'Filters.isolatedConnect',
              'Filters.glenoidMouldDesign' : ('Filters',),
              'Filters.landmarkTransform' : ('Filters',),
              'Filters.marchingCubes' : ('Filters',),
              'Filters.polyDataConnect' : ('Filters',),
              'Filters.polyDataNormals' : ('Filters',),
              'Filters.resampleImage' : ('Filters',),
              'Filters.seedConnect' : ('Filters',),
              'Filters.shellSplatSimple' : ('Filters',),
              'Filters.transformPolyData' : ('Filters',),
              'Filters.wsMeshSmooth' : ('Filters',),

              'Writers.ivWRT' : ('Writers',),
              'Writers.stlWRT' : ('Writers',),
              'Writers.vtiWRT' : ('Writers',),
              'Writers.vtpWRT' : ('Writers',),
              'Writers.vtkPolyDataWRT' : ('Writers',),
              'Writers.vtkStructPtsWRT' : ('Writers',),

              'Misc.superQuadric' : ('Sources',),
              'Misc.implicitToVolume' : ('Sources',),              
              
              'ifdoc.ifdocRDR' : ('ifdoc',),
              'ifdoc.ifdocVWR' : ('ifdoc',),

              'Insight.gradientAnisotropicDiffusion' : ('Insight',),
              'Insight.curvatureAnisotropicDiffusion' : ('Insight',),
              'Insight.geodesicActiveContour' : ('Insight',),
              'Insight.imageStackRDR' : ('Insight',),
              'Insight.register2D' : ('Insight',),
              'Insight.transform2D' : ('Insight',),
              'Insight.transformStackWRT' : ('Insight',),
              'Insight.transformStackRDR' : ('Insight',),
              'Insight.VTKtoITKF3' : ('Insight',),
              'Insight.ITKF3toVTK' : ('Insight',)              
              }




