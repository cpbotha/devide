# snippet that illustrates programmatic setting of Window/Level
# in the slice3dVWR introspection interface

W = 500
L = 1000

sds = obj.sliceDirections._sliceDirectionsDict.values()
for sd in sds:
    ipw = sd._ipws[0]
    ipw.SetWindowLevel(W, L, 0)
