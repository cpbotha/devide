# EXPERIMENTAL.  DO NOT USE UNLESS YOU ARE JORIK.

import vtk

sv = devideApp.moduleManager.getMarkedModule('slice3dVWR')

if sv:
    ipw = sv.sliceDirections._sliceDirectionsDict.values()[0]._ipws[0]
    #print ipw.GetLookupTable().GetWindow()
    
    lut = vtk.vtkLookupTable()
    lut.SetTableRange(-2100, 3000)
    lut.SetHueRange(0.1, 1)
    lut.SetSaturationRange(1.0, 1.0)
    lut.SetValueRange(1.0, 1.0)
    lut.SetAlphaRange(1.0, 1.0)
    lut.Build()
    
    ipw.SetUserControlledLookupTable(1)
    ipw.SetLookupTable(lut)
    
    
else:
    print "You have to mark a slice3dVWR module!"
