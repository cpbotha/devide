from wxPython.wx import *
import string
import traceback
import vtk

def logError(msg):
    # create nice formatted string with tracebacks and all
    dmsg = \
         string.join(traceback.format_exception(sys.exc_type,
                                                sys.exc_value,
                                                sys.exc_traceback))
    # we can't disable the timestamp yet
    # wxLog_SetTimestamp()
    # set the detail message
    wxLogError(dmsg)
    # then the most recent
    wxLogError(msg)
    # and flush... the last message will be the actual error
    # message, what we did before will add to it to become the
    # detail message
    wxLog_FlushActive()

def flattenProp3D(prop3D):
    """Get rid of the UserTransform() of an actor by integrating it with
    the 'main' matrix.
    """

    if not prop3D.GetUserTransform():
        # no flattening here, move along
        return

    # get the current "complete" matrix (combining internal and user)
    currentMatrix = vtk.vtkMatrix4x4()
    prop3D.GetMatrix(currentMatrix)
    # apply it to a transform
    currentTransform = vtk.vtkTransform()
    currentTransform.Identity()
    currentTransform.SetMatrix(currentMatrix)

    # zero the prop3D UserTransform
    prop3D.SetUserTransform(None)

    # and set the internal matrix of the prop3D
    prop3D.SetPosition(currentTransform.GetPosition())
    prop3D.SetScale(currentTransform.GetScale())    
    prop3D.SetOrientation(currentTransform.GetOrientation())

    # we should now also be able to zero the origin
    #prop3D.SetOrigin(0,0,0)
    

def textToFloat(text, defaultFloat):
    """Converts text to a float by using an eval and returns the float.
    If something goes wrong, returns defaultFloat.
    """

    try:
        returnFloat = float(eval(text))
    except Exception:
        returnFloat = defaultFloat

    return returnFloat

def textToInt(text, defaultInt):
    """Converts text to an integer by using an eval and returns the integer.
    If something goes wrong, returns default Int.
    """

    try:
        returnInt = int(eval(text))
    except Exception:
        returnInt = defaultInt

    return returnInt

