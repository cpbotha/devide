# __init__.py by Charl P. Botha <cpbotha@ieee.org>
# $Id: __init__.py,v 1.61 2003/12/18 11:11:19 cpbotha Exp $
# contains list of built-in modules; update when adding new modules
# the user_modules get listed automatically

# we HAVE to hard-code this list, because all these modules will be frozen
# along with the application... we can't search directories.

moduleList = ['Readers.dicomRDR',
              'Readers.objRDR',
              'Readers.rawVolumeRDR',
              'Readers.stlRDR',
              'Readers.vtiRDR',
              'Readers.vtkPolyDataRDR',
              'Readers.vtkStructPtsRDR',

              'Viewers.slice3dVWR',

              'Filters.appendPolyData',
              'Filters.contour',
              'Filters.decimate',
              'Filters.doubleThreshold',
              'Filters.imageFlip',
              'Filters.imageGaussianSmooth',
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
              'Writers.vtkPolyDataWRT',
              'Writers.vtkStructPtsWRT',
              
              'ifdoc.ifdocRDR',
              'ifdoc.ifdocVWR',

              'Insight.imageStackRDR',
              'Insight.register2D',
              'Insight.transform2D',
              'Insight.transformStackWRT',
              'Insight.transformStackRDR']




