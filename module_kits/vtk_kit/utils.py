# $Id$

"""Utility methods for vtk_kit module kit.

@author Charl P. Botha <http://cpbotha.net/>
"""

import vtk

def setup_renderers(renwin, fg_ren, bg_ren):
    """Utility method to configure foreground and background renderer
    and insert them into different layers of the renderenwinindow.

    Use this if you want an incredibly cool gradient background!
    """
    
    # bit of code thanks to 
    # http://www.bioengineering-research.com/vtk/BackgroundGradient.tcl
    # had to change approach though to using background renderer,
    # else transparent objects don't appear, and adding flat
    # shaded objects breaks the background gradient.
    # =================================================================
    
    qpts = vtk.vtkPoints()
    qpts.SetNumberOfPoints(4)
    qpts.InsertPoint(0, 0, 0, 0)
    qpts.InsertPoint(1, 1, 0, 0)
    qpts.InsertPoint(2, 1, 1, 0)
    qpts.InsertPoint(3, 0, 1, 0)

    quad = vtk.vtkQuad()
    quad.GetPointIds().SetId(0,0)
    quad.GetPointIds().SetId(1,1)
    quad.GetPointIds().SetId(2,2)
    quad.GetPointIds().SetId(3,3)

    uc = vtk.vtkUnsignedCharArray()
    uc.SetNumberOfComponents(4)
    uc.SetNumberOfTuples(4)
    uc.SetTuple4(0, 128, 128, 128, 255) # bottom left RGBA
    uc.SetTuple4(1, 128, 128, 128, 255) # bottom right RGBA
    uc.SetTuple4(2, 255, 255, 255, 255) # top right RGBA
    uc.SetTuple4(3, 255, 255, 255, 255) # tob left RGBA

    dta = vtk.vtkPolyData()
    dta.Allocate(1,1)
    dta.InsertNextCell(quad.GetCellType(), quad.GetPointIds())
    dta.SetPoints(qpts)
    dta.GetPointData().SetScalars(uc)

    coord = vtk.vtkCoordinate()
    coord.SetCoordinateSystemToNormalizedDisplay()

    mapper2d = vtk.vtkPolyDataMapper2D()
    mapper2d.SetInput(dta)
    mapper2d.SetTransformCoordinate(coord)

    actor2d = vtk.vtkActor2D()
    actor2d.SetMapper(mapper2d)
    actor2d.GetProperty().SetDisplayLocationToBackground()

    bg_ren.AddActor(actor2d)
    bg_ren.SetLayer(0) # seems to be background
    bg_ren.SetInteractive(0)

    fg_ren.SetLayer(1) # and foreground

    renwin.SetNumberOfLayers(2)
    renwin.AddRenderer(fg_ren)
    renwin.AddRenderer(bg_ren)

