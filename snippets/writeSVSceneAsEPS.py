# $Id: writeSVSceneAsEPS.py,v 1.1 2005/02/11 08:53:45 cpbotha Exp $

import vtk

className = obj.__class__.__name__
if className == 'slice3dVWR':
    rw = obj._threedRenderer.GetRenderWindow()
    try:
        e = vtk.vtkGL2PSExporter()
    except AttributeError:
        print "Your VTK was compiled without GL2PS support."
        
    else:
        e.SetRenderWindow(rw)
        e.SetFilePrefix('slice3dVWRscene')
        e.SetSortToBSP()
        e.SetDrawBackground(0)
        e.Write()

else:
    print "You have to run this from the introspection window of a slice3dVWR."
