# __init__.py by Charl P. Botha <cpbotha@ieee.org>
# $Id: __init__.py,v 1.39 2003/09/19 23:54:16 cpbotha Exp $
# contains list of built-in modules; update when adding new modules
# the user_modules get listed automatically

# we HAVE to hard-code this list, because all these modules will be frozen
# along with the application... we can't search directories.

module_list = ['appendPolyDataFLT',
               'contourFLT',
               'dicomRDR',
               'decimateFLT',
               'doubleThresholdFLT',
               'glenoidMouldDesignFLT',
               'hdfRDR',
               'ifdocRDR',
               'ifdocVWR',               
               'marchingCubesFLT',
               'polyDataConnectFLT',
               'polyDataNormalsFLT',
               'rawVolumeRDR',
               'seedConnectFLT',
               'shellSplatSimpleFLT',
	       'slice3dVWR',
               'stlRDR',
               'stlWRT',
               'vtkPolyDataRDR',
               'vtkPolyDataWRT',
               'vtkStructPtsRDR',               
               'vtkStructPtsWRT',
               'wsMeshSmoothFLT']

moduleList = ['Readers.hdfRDR',
              'Readers.dicomRDR',
              'Filters.doubleThreshold',
              'Writers.vtkPolyDataWRT']

