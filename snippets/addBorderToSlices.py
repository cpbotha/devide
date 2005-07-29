import vtk
import wx

def makeBorderPD(ipw):

    # setup source
    ps = vtk.vtkPlaneSource()
    ps.SetOrigin(ipw.GetOrigin())
    ps.SetPoint1(ipw.GetPoint1())
    ps.SetPoint2(ipw.GetPoint2())

    fe = vtk.vtkFeatureEdges()
    fe.SetInput(ps.GetOutput())

    tubef = vtk.vtkTubeFilter()
    tubef.SetNumberOfSides(12)
    tubef.SetRadius(0.5)
    tubef.SetInput(fe.GetOutput())

    return tubef.GetOutput()

className = obj.__class__.__name__
if className == 'slice3dVWR':

    sds = obj.sliceDirections.getSelectedSliceDirections()
    
    if len(sds) > 0:

        apd = vtk.vtkAppendPolyData()

        for sd in sds:
            for ipw in sd._ipws:
                apd.AddInput(makeBorderPD(ipw))

        mapper = vtk.vtkPolyDataMapper()
        mapper.ScalarVisibilityOff()
        mapper.SetInput(apd.GetOutput())

        actor = vtk.vtkActor()
        actor.GetProperty().SetColor(0.0, 0.0, 1.0)
        actor.SetMapper(mapper)

        if hasattr(obj._threedRenderer, 'addBorderToSlicesActor'):
            obj._threedRenderer.RemoveProp(
                obj._threedRenderer.addBorderToSlicesActor)

        obj._threedRenderer.AddProp(actor)
        obj._threedRenderer.addBorderToSlicesActor = actor

    else:
        print "Please select the slices whose opacity you want to set."
    
    
else:
    print "You have to run this from a slice3dVWR introspect window."
