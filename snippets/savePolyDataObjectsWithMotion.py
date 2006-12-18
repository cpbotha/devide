# snippet to save polydata of all selected objects to disc, transformed with
# the currently active object motion for that object.  This snippet should be
# run within a slice3dVWR introspection context.
# $Id$

import os
import tempfile
import vtk

className = obj.__class__.__name__

if className == 'slice3dVWR':

    # find all polydata objects
    so = obj._tdObjects._getSelectedObjects()
    polyDatas = [pd for pd in so if hasattr(pd, 'GetClassName') and
                 pd.GetClassName() == 'vtkPolyData']

    # now find their actors
    objectsDict = obj._tdObjects._tdObjectsDict
    actors = [objectsDict[pd]['vtkActor'] for pd in polyDatas]
    # combining this with the previous statement is more effort than it's worth
    names = [objectsDict[pd]['objectName'] for pd in polyDatas]

    # now iterate through both, writing each transformed polydata
    trfm = vtk.vtkTransform()
    mtrx = vtk.vtkMatrix4x4()
    trfmPd = vtk.vtkTransformPolyDataFilter()
    trfmPd.SetTransform(trfm)
    vtpWriter = vtk.vtkXMLPolyDataWriter()
    vtpWriter.SetInput(trfmPd.GetOutput())
    
    tempdir = tempfile.gettempdir()

    for pd,actor,name in zip(polyDatas,actors,names):
        actor.GetMatrix(mtrx)
        trfm.Identity()
        trfm.SetMatrix(mtrx)
        trfmPd.SetInput(pd)
        filename = os.path.join(tempdir, '%s.vtp' % (name,))
        vtpWriter.SetFileName(filename)
        print "Writing %s." % (filename,)
        vtpWriter.Write()

else:
    print "This snippet must be run from a slice3dVWR introspection window."
