# this snippet will rotate the camera in the slice3dVWR that you have
# selected and dump every frame as a PNG to the temporary directory
# you can modify this snippet if you want to make movies of for instance
# deforming surfaces and whatnot

# 1. right click on a slice3dVWR in the graphEditor
# 2. select "Mark Module" from the drop-down menu
# 3. accept "slice3dVWR" as suggestion for the mark index name
# 4. do the same for your superQuadric (select 'superQuadric' as index name)
# 5. execute this snippet

import os
import tempfile
import vtk
import wx

# get the slice3dVWR marked by the user
sv = devideApp.moduleManager.getMarkedModule('slice3dVWR')
sq = devideApp.moduleManager.getMarkedModule('superQuadric')

if sv and sq:
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
    for i in range(2 * 36):
        sq._superquadricSource.SetPhiRoundness(i / 36.0)
        camera.Azimuth(10)
        sv.render3D()

        # make sure w2i knows it's a new image
        w2i.Modified()
        pngWriter.SetFileName('%s%03d.png' % (fprefix, i))
        pngWriter.Write()

    print "The frames have been written as %s*.png." % (fprefix,)

else:
    print "You have to mark a slice3dVWR module and a superQuadric module!"
