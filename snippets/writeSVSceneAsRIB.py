# $Id: writeSVSceneAsRIB.py,v 1.1 2005/07/28 16:53:35 cpbotha Exp $

# to use a shader on an actor, do this first before export:
# a = vtk.vtkRIBProperty()
# a.SetVariable('Km', 'float')
# a.SetParameter('Km', '1')
# a.SetDisplacementShader('dented')
# actor.SetProperty(a)

import os
import tempfile
import vtk

className = obj.__class__.__name__
if className == 'slice3dVWR':
    rw = obj._threedRenderer.GetRenderWindow()

    e = vtk.vtkRIBExporter()
    e.SetRenderWindow(rw)
    tempdir = tempfile.gettempdir()
    outputfilename = os.path.join(tempdir, 'slice3dVWRscene')
    e.SetFilePrefix(outputfilename)
    obj._orientationWidget.Off()
    e.Write()
    obj._orientationWidget.On()
    
    print "Wrote file to %s.rib." % (outputfilename,)

else:
    print "You have to run this from the introspection window of a slice3dVWR."
