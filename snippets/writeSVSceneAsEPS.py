# $Id: writeSVSceneAsEPS.py,v 1.2 2005/02/11 09:09:55 cpbotha Exp $

import os
import tempfile
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
        tempdir = tempfile.gettempdir()
        outputfilename = os.path.join(tempdir, 'slice3dVWRscene')
        e.SetFilePrefix(outputfilename)
        e.SetSortToBSP()
        e.SetDrawBackground(0)
        e.SetCompress(0)
        obj._orientationWidget.Off()
        e.Write()
        obj._orientationWidget.On()
        
        print "Wrote file to %s." % (outputfilename,)

else:
    print "You have to run this from the introspection window of a slice3dVWR."
