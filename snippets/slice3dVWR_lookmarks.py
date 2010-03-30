def get_plane_infos():
    # get out all plane orientations and normals
    plane_infos = []
    for sd in obj.sliceDirections._sliceDirectionsDict.values():
        # each sd has at least one IPW
        ipw = sd._ipws[0]
        plane_infos.append((ipw.GetOrigin(), ipw.GetPoint1(), ipw.GetPoint2(), ipw.GetWindow(), ipw.GetLevel()))

    return plane_infos

def set_plane_infos(plane_infos):
    # go through existing sliceDirections, sync if info available
    sds = obj.sliceDirections._sliceDirectionsDict.values()
    for i in range(len(sds)):
        sd = sds[i]
        if i < len(plane_infos):
            pi = plane_infos[i]            
            ipw = sd._ipws[0]
            ipw.SetOrigin(pi[0])
            ipw.SetPoint1(pi[1])
            ipw.SetPoint2(pi[2])
            ipw.SetWindowLevel(pi[3], pi[4], 0)
            sd._syncAllToPrimary()


def get_camera_info():
    cam = obj._threedRenderer.GetActiveCamera()
    p = cam.GetPosition()
    vu = cam.GetViewUp()
    fp = cam.GetFocalPoint()
    ps = cam.GetParallelScale()
    return (p, vu, fp, ps)

def get_lookmark():
    return (get_plane_infos(), get_camera_info())

def set_lookmark(lookmark):
    # first setup the camera
    ci = lookmark[1]
    cam = obj._threedRenderer.GetActiveCamera()
    cam.SetPosition(ci[0])
    cam.SetViewUp(ci[1])
    cam.SetFocalPoint(ci[2])
    # required for parallel projection
    cam.SetParallelScale(ci[3])
    
    # also needed to adapt correctly to new camera
    ren = obj._threedRenderer
    ren.UpdateLightsGeometryToFollowCamera()
    ren.ResetCameraClippingRange()

    # now do the planes
    set_plane_infos(lookmark[0])

    obj.render3D()
