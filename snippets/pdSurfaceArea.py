# this DeVIDE snippet will determine the surface area of all selected
# 3D objects in a marked slice3dVWR

# in short:
# 1. right click on a slice3dVWR in the graphEditor
# 2. select "Mark Module" from the drop-down menu
# 3. accept "slice3dVWR" as suggestion for the mark index name
# 4. execute this snippet

import vtk

# get the slice3dVWR marked by the user
sv = devideApp.moduleManager.getMarkedModule('slice3dVWR')

if sv:
    so = sv._tdObjects._getSelectedObjects()
    polyDatas = [pd for pd in so if hasattr(pd, 'GetClassName') and
                 pd.GetClassName() == 'vtkPolyData']
    
    tf = vtk.vtkTriangleFilter()
    mp = vtk.vtkMassProperties()
    mp.SetInput(tf.GetOutput())
    
    for pd in polyDatas:
        tf.SetInput(pd)
        mp.Update()
        print "AREA == %f" % (mp.GetSurfaceArea(),)

else:
    print "You have to mark a slice3dVWR module!"

    
