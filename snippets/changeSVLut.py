# EXPERIMENTAL.  DO NOT USE UNLESS YOU ARE JORIK. (OR JORIS)

import vtk

className = obj.__class__.__name__
if className == 'slice3dVWR':
    ipw = obj.sliceDirections._sliceDirectionsDict.values()[0]._ipws[0]
    
    if ipw.GetInput():
        mins, maxs = ipw.GetInput().GetScalarRange()
    else:
        mins, maxs = 1, 1000000
        
    lut = vtk.vtkLookupTable()
    lut.SetTableRange(mins, maxs)
    lut.SetHueRange(0.1, 1.0)
    lut.SetSaturationRange(1.0, 1.0)
    lut.SetValueRange(1.0, 1.0)
    lut.SetAlphaRange(1.0, 1.0)
    lut.Build()
    
    ipw.SetUserControlledLookupTable(1)
    ipw.SetLookupTable(lut)
    
    
else:
    print "You have to mark a slice3dVWR module!"
