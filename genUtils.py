from wxPython.wx import *
import string
import traceback
import vtk

def clampVariable(v, min, max):
    """Make sure variable is on the range [min,max].  Return clamped variable.
    """
    if v < min:
        v = min
    elif v > max:
        v = max

    return v

def logError(msg):
    # create nice formatted string with tracebacks and all
    ei = sys.exc_info()
    dmsg = \
         string.join(traceback.format_exception(ei[0],
                                                ei[1],
                                                ei[2]))
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

def logWarning(msg):
    # create nice formatted string with tracebacks and all
    ei = sys.exc_info()
    dmsg = \
         string.join(traceback.format_exception(ei[0],
                                                ei[1],
                                                ei[2]))
    # we can't disable the timestamp yet
    # wxLog_SetTimestamp()
    # set the detail message
    wxLogWarning(dmsg)
    # then the most recent
    wxLogWarning(msg)
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

def planePlaneIntersection(
    planeNormal0, planeOrigin0, planeNormal1, planeOrigin1):
    """Given two plane definitions, determine the intersection line using
    the method on page 233 of Graphics Gems III: 'Plane-to-Plane Intersection'

    Returns tuple with lineOrigin and lineVector.
    
    """

    # convert planes to Hessian form first:
    # http://mathworld.wolfram.com/HessianNormalForm.html

    # calculate p, orthogonal distance from the plane to the origin
    p0 = - vtk.vtkMath.Dot(planeOrigin0, planeNormal0)
    p1 = - vtk.vtkMath.Dot(planeOrigin1, planeNormal1)
    # we already have n, the planeNormal

    # calculate cross product
    L = [0.0, 0.0, 0.0]
    vtk.vtkMath.Cross(planeNormal0, planeNormal1, L)
    absL = [abs(e) for e in L]
    maxAbsL = max(absL)
    
    if maxAbsL == 0.0:
        raise ValueError, "Planes are almost parallel."
    
    w = absL.index(maxAbsL)
    Lw = L[w]
    # we're going to set the maxLidx'th component of our lineOrigin (i.e.
    # any point on the line) to 0

    P = [0.0, 0.0, 0.0]

    # we want either [0, 1], [1, 2] or [2, 0]
    if w == 0:
        u = 1
        v = 2
    elif w == 1:
        u = 2
        v = 0
    else:
        u = 0
        v = 1
    
    P[u] = (planeNormal0[v] * p1 - planeNormal1[v] * p0) / float(Lw)
    P[v] = (planeNormal1[u] * p0 - planeNormal0[u] * p1) / float(Lw)
    P[w] = 0 # just for completeness

    vtk.vtkMath.Normalize(L)

    return (P, L)

def setGridCellYesNo(grid, row, col, yes=True):
    if yes:
        colour = wxColour(0,255,0)
        text = '1'
    else:
        colour = wxColour(255,0,0)
        text = '0'
        
    grid.SetCellValue(row, col, text)
    grid.SetCellBackgroundColour(row, col, colour)

def textToFloat(text, defaultFloat):
    """Converts text to a float by using an eval and returns the float.
    If something goes wrong, returns defaultFloat.
    """

    try:
        returnFloat = float(text)
    except Exception:
        returnFloat = defaultFloat

    return returnFloat

def textToInt(text, defaultInt):
    """Converts text to an integer by using an eval and returns the integer.
    If something goes wrong, returns default Int.
    """

    try:
        returnInt = int(text)
    except Exception:
        returnInt = defaultInt

    return returnInt

def textToTuple(text, defaultTuple):
    """This will convert the text representation of a tuple into a real
    tuple.  No checking for type or number of elements is done.  See
    textToTypeTuple for that.
    """

    # first make sure that the text starts and ends with brackets
    text = text.strip()
    
    if text[0] != '(':
        text = '(%s' % (text,)

    if text[-1] != ')':
        text = '%s)' % (text,)

    try:
        returnTuple = eval('tuple(%s)' % (text,))
    except Exception:
        returnTuple = defaultTuple

    return returnTuple

def textToTypeTuple(text, defaultTuple, numberOfElements, aType):
    """This will convert the text representation of a tuple into a real
    tuple with numberOfElements elements, all of type aType.  If the required
    number of elements isn't available, or they can't all be casted to the
    correct type, the defaultTuple will be returned.
    """
    
    aTuple = textToTuple(text, defaultTuple)

    if len(aTuple) != numberOfElements:
        returnTuple = defaultTuple

    else:
        try:
            returnTuple = tuple([aType(e) for e in aTuple])
        except ValueError:
            returnTuple = defaultTuple

    return returnTuple

