# to use this code:
# 1. load into slice3dVWR introspection window
# 2. execute with ctrl-enter or File | Run current edit
# 3. in the bottom window type lm1 = get_lookmark()
# 4. do stuff
# 5. to restore lookmark, do set_lookmark(lm1)

# keep on bugging me to:
# 1. fix slice3dVWR
# 2. build this sort of functionality into the GUI

# cpbotha

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
            ipw.UpdatePlacement()
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

def reset_to_default_view(view_index):
    """
    @param view_index 0 for YZ, 1 for ZX, 2 for XY
    """

    cam = obj._threedRenderer.GetActiveCamera()
    fp = cam.GetFocalPoint()
    cp = cam.GetPosition()

    if view_index == 0:
        cam.SetViewUp(0,1,0)
        if cp[0] < fp[0]:
            x = fp[0] + (fp[0] - cp[0])
        else:
            x = cp[0]

        # safety check so we don't put cam in focal point
        # (renderer gets into unusable state!)
        if x == fp[0]:
            x = fp[0] + 1

        cam.SetPosition(x, fp[1], fp[2])

    elif view_index == 1:
        cam.SetViewUp(0,0,1)
        if cp[1] < fp[1]:
            y = fp[1] + (fp[1] - cp[1])
        else:
            y = cp[1]

        if y == fp[1]:
            y = fp[1] + 1


        cam.SetPosition(fp[0], y, fp[2])

    elif view_index == 2:
        # then make sure it's up is the right way
        cam.SetViewUp(0,1,0)
        # just set the X,Y of the camera equal to the X,Y of the
        # focal point.
        if cp[2] < fp[2]:
            z = fp[2] + (fp[2] - cp[2])
        else:
            z = cp[2]

        if z == fp[2]:
            z = fp[2] + 1


        cam.SetPosition(fp[0], fp[1], z)

    # first reset the camera
    obj._threedRenderer.ResetCamera()
    obj.render3D()
        
