# link cameras of all selected slice3dVWRs
# after having run this, all selected slice3dVWRs will have linked
# cameras, so if you change the view in anyone, all will follow.

# 1. run this in the main DeVIDE introspection window after having
#    selected a number of slice3dVWRs

# 2. to unlink views, type unlink_slice3dVWRs() in the bottom
#    interpreter window.

def observer_istyle(s3d, s3ds):
    cam = s3d._threedRenderer.GetActiveCamera()
    pos = cam.GetPosition()
    fp = cam.GetFocalPoint()
    vu = cam.GetViewUp()

    for other_s3d in s3ds:
        if not other_s3d is s3d:
            other_ren = other_s3d._threedRenderer
            other_cam = other_ren.GetActiveCamera()
            other_cam.SetPosition(pos)
            other_cam.SetFocalPoint(fp)
            other_cam.SetViewUp(vu)
            other_ren.UpdateLightsGeometryToFollowCamera()
            other_ren.ResetCameraClippingRange()
            other_s3d.render3D()

def unlink_slice3dVWRs():
    for s3d in s3ds:
        istyle = s3d.threedFrame.threedRWI.GetInteractorStyle()
        istyle.RemoveObservers('InteractionEvent') # more or less safe


iface = devide_app.get_interface()
sg = iface._graph_editor._selected_glyphs.getSelectedGlyphs()
s3ds = [i.module_instance for i in sg if i.module_instance.__class__.__name__ == 'slice3dVWR']

unlink_slice3dVWRs()
for s3d in s3ds:
    ren = s3d._threedRenderer
    istyle = s3d.threedFrame.threedRWI.GetInteractorStyle()
    istyle.AddObserver('InteractionEvent', lambda o,e,s3d=s3d: observer_istyle(s3d,s3ds))

        



