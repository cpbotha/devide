# __init__.py by Charl P. Botha <cpbotha@ieee.org>
# $Id: __init__.py,v 1.40 2003/09/20 21:50:18 cpbotha Exp $
# contains list of built-in modules; update when adding new modules
# the user_modules get listed automatically

# we HAVE to hard-code this list, because all these modules will be frozen
# along with the application... we can't search directories.

moduleList = ['Readers.dicomRDR',
              'Readers.hdfRDR',
              'Readers.ifdocRDR',
              'Readers.dicomRDR',
              'Readers.rawVolumeRDR',
              'Readers.stlRDR',
              'Readers.vtkPolyDataRDR',
              'Readers.vtkStructPtsRDR',

              'Viewers.ifdocVWR',
              'Viewers.slice3dVWR',

              'Filters.appendPolyData',
              'Filters.contour',
              'Filters.decimate',
              'Filters.doubleThreshold',
              'Filters.glenoidMouldDesign',
              'Filters.marchingCubes',
              'Filters.polyDataConnect',
              'Filters.polyDataNormals',
              'Filters.seedConnect',
              'Filters.shellSplatSimple',
              'Filters.wsMeshSmooth',
              
              'Writers.stlWRT',
              'Writers.vtkPolyDataWRT'
              'Writers.vtkStructPtsWRT']
