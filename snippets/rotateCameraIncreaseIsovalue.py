# this snippet will rotate the camera in the slice3dVWR that you have
# selected whilst slowly increasing the isovalue of the marchingCubes that
# you have selected and dump every frame as a PNG to the temporary directory
# this is ideal for making movies of propagating surfaces in distance fields

# 1. right click on a slice3dVWR in the graphEditor
# 2. select "Mark Module" from the drop-down menu
# 3. accept "slice3dVWR" as suggestion for the mark index name
# 4. do the same for your marchingCubes (select 'marchingCubes' as index name)
# 5. execute this snippet

import os
import tempfile
import vtk
import wx

# get the slice3dVWR marked by the user
sv = devideApp.ModuleManager.getMarkedModule('slice3dVWR')
mc = devideApp.ModuleManager.getMarkedModule('marchingCubes')

if sv and mc:
    # bring the window to the front
    sv.view()
    # make sure it actually happens
    wx.Yield()
    
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(sv._threedRenderer.GetRenderWindow())
    pngWriter = vtk.vtkPNGWriter()
    pngWriter.SetInput(w2i.GetOutput())

    tempdir = tempfile.gettempdir()
    fprefix = os.path.join(tempdir, 'devideFrame')
    
    camera = sv._threedRenderer.GetActiveCamera()
    for i in range(160):
        print i
        mc._contourFilter.SetValue(0,i / 2.0)
        camera.Azimuth(5)
        sv.render3D()

        # make sure w2i knows it's a new image
        w2i.Modified()
        pngWriter.SetFileName('%s%03d.png' % (fprefix, i))
        pngWriter.Write()

    print "The frames have been written as %s*.png." % (fprefix,)

else:
    print "You have to mark a slice3dVWR module and a marchingCubes module!"
