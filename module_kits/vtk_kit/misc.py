# $Id$

"""Miscellaneous functions that are part of the vtk_kit.

This module is imported by vtk_kit.init() after the rest of the vtk_kit has
been initialised.  To use these functions in your module code, do e.g.:
import moduleKits; moduleKits.vtk_kit.misc.flatterProp3D(obj);

@author: Charl P. Botha <http://cpbotha.net/>
"""

# this import does no harm; we go after the rest of vtk_kit has been
# initialised
import vtk

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
