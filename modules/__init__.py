# __init__.py by Charl P. Botha <cpbotha@ieee.org>
# $Id: __init__.py,v 1.50 2003/10/16 09:43:59 cpbotha Exp $
# contains list of built-in modules; update when adding new modules
# the user_modules get listed automatically

# we HAVE to hard-code this list, because all these modules will be frozen
# along with the application... we can't search directories.

moduleList = ['Readers.dicomRDR',
              'Readers.hdfRDR',
              'Readers.objRDR',
              'Readers.rawVolumeRDR',
              'Readers.stlRDR',
              'Readers.vtkPolyDataRDR',
              'Readers.vtkStructPtsRDR',

              'Viewers.slice3dVWR',

              'Filters.appendPolyData',
              'Filters.contour',
              'Filters.decimate',
              'Filters.doubleThreshold',
              'Filters.imageGaussianSmooth',
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
              'Writers.vtkPolyDataWRT',
              'Writers.vtkStructPtsWRT',
              
              'ifdoc.ifdocRDR',
              'ifdoc.ifdocVWR']
