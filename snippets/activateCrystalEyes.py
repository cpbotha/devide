import vtk

className = obj.__class__.__name__

if className == 'slice3dVWR':
    rw = obj.threedFrame.threedRWI.GetRenderWindow()
    rw.SetStereoTypeToCrystalEyes()
    #rw.SetStereoTypeToRedBlue()
    rw.SetStereoRender(1)
    rw.Render()

else:
    print "This snippet must be run from a slice3dVWR introspection window."
