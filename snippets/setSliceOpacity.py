import vtk
import wx

className = obj.__class__.__name__
if className == 'slice3dVWR':

    sds = obj.sliceDirections.getSelectedSliceDirections()
    
    if len(sds) > 0:

        opacityText = wx.GetTextFromUser(
            'Enter a new opacity value (0.0 to 1.0) for all selected '
            'slices.')

        opacity = -1.0
        try:
            opacity = float(opacityText)
        except ValueError:
            pass

        if opacity < 0.0 or opacity > 1.0:
            print "Invalid opacity."

        else:
            for sd in sds:
                for ipw in sd._ipws:
                    prop = ipw.GetTexturePlaneProperty()
                    prop.SetOpacity(opacity)

    else:
        print "Please select the slices whose opacity you want to set."
    
    
else:
    print "You have to run this from a slice3dVWR introspect window."
