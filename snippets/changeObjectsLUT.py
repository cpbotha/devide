# snippet to change the LookupTables (colourmaps) of the selected objects
# this should be run in the introspection context of a slice3dVWR
# $Id: changeObjectsLUT.py,v 1.1 2004/11/16 15:52:09 cpbotha Exp $

import os
import tempfile
import vtk

className = obj.__class__.__name__

if className == 'slice3dVWR':

    # find all polydata objects
    so = obj._tdObjects._getSelectedObjects()
    polyDatas = [pd for pd in so if hasattr(pd, 'GetClassName') and
                 pd.GetClassName() == 'vtkPolyData']

    # now find their Mappers
    objectsDict = obj._tdObjects._tdObjectsDict
    actors = [objectsDict[pd]['vtkActor'] for pd in polyDatas]
    mappers = [a.GetMapper() for a in actors]
    
    for mapper in mappers:
        lut = mapper.GetLookupTable()
        #lut.SetScaleToLog10()
        lut.SetScaleToLinear()
        
        #srange = mapper.GetInput().GetScalarRange()
        #lut.SetTableRange(srange)
        #lut.SetSaturationRange(1.0,1.0)
        #lut.SetValueRange(1.0, 1.0)
        #lut.SetHueRange(0.1, 1.0)
        
        lut.Build()

else:
    print "This snippet must be run from a slice3dVWR introspection window."
