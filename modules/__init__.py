# __init__.py by Charl P. Botha <cpbotha@ieee.org>
# $Id: __init__.py,v 1.63 2004/02/13 14:36:58 cpbotha Exp $
# contains list of built-in modules; update when adding new modules
# the user_modules get listed automatically

# we HAVE to hard-code this list, because all these modules will be frozen
# along with the application... we can't search directories.

moduleList = ['Readers.dicomRDR',
              'Readers.objRDR',
              'Readers.rawVolumeRDR',
              'Readers.stlRDR',
              'Readers.vtiRDR',
              'Readers.vtpRDR',
              'Readers.vtkPolyDataRDR',
              'Readers.vtkStructPtsRDR',

              'Viewers.slice3dVWR',

              'Filters.appendPolyData',
              'Filters.contour',
              'Filters.decimate',
              'Filters.doubleThreshold',
              'Filters.imageFlip',
              'Filters.imageGaussianSmooth',
              'Filters.imageGradientMagnitude',
              'Filters.imageMask',
              'Filters.imageMedian3D',
              #'Filters.isolatedConnect',
              'Filters.glenoidMouldDesign',
              'Filters.landmarkTransform',
              'Filters.marchingCubes',
              'Filters.polyDataConnect',
              'Filters.polyDataNormals',
              'Filters.resampleImage',
              'Filters.seedConnect',
              'Filters.shellSplatSimple',
              'Filters.transformPolyData',
              'Filters.wsMeshSmooth',

              'Writers.ivWRT',
              'Writers.stlWRT',
              'Writers.vtiWRT',
              'Writers.vtpWRT',
              'Writers.vtkPolyDataWRT',
              'Writers.vtkStructPtsWRT',
              
              'ifdoc.ifdocRDR',
              'ifdoc.ifdocVWR',

              'Insight.imageStackRDR',
              'Insight.register2D',
              'Insight.transform2D',
              'Insight.transformStackWRT',
              'Insight.transformStackRDR']




