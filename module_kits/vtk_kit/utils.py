# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

"""Utility methods for vtk_kit module kit.

@author Charl P. Botha <http://cpbotha.net/>
"""

import vtk

class DVOrientationWidget:
    """Convenience class for embedding orientation widget in any
    renderwindowinteractor.  If the data has DeVIDE style orientation
    metadata, this class will show the little LRHFAP block, otherwise
    x-y-z cursor.
    """

    def __init__(self, rwi):


        self._orientation_widget = vtk.vtkOrientationMarkerWidget()
        self._orientation_widget.SetInteractor(rwi)

        # we'll use this if there is no orientation metadata
        # just a thingy with x-y-z indicators
        self._axes_actor = vtk.vtkAxesActor()

        # we'll use this if there is orientation metadata
        self._annotated_cube_actor = aca = vtk.vtkAnnotatedCubeActor()

        # configure the thing with better colours and no stupid edges 
        #aca.TextEdgesOff()
        aca.GetXMinusFaceProperty().SetColor(1,0,0)
        aca.GetXPlusFaceProperty().SetColor(1,0,0)
        aca.GetYMinusFaceProperty().SetColor(0,1,0)
        aca.GetYPlusFaceProperty().SetColor(0,1,0)
        aca.GetZMinusFaceProperty().SetColor(0,0,1)
        aca.GetZPlusFaceProperty().SetColor(0,0,1)
       

    def close(self):
        self.set_input(None)
        self._orientation_widget.SetInteractor(None)


    def set_input(self, input_data):
        if input_data is None:
            self._orientation_widget.Off()
            return

        ala = input_data.GetFieldData().GetArray('axis_labels_array')
        if ala:
            lut = list('LRPAFH')
            labels = []
            for i in range(6):
                labels.append(lut[ala.GetValue(i)])
                
            self._set_annotated_cube_actor_labels(labels)
            self._orientation_widget.Off()
            self._orientation_widget.SetOrientationMarker(
                self._annotated_cube_actor)
            self._orientation_widget.On()
            
        else:
            self._orientation_widget.Off()
            self._orientation_widget.SetOrientationMarker(
                self._axes_actor)
            self._orientation_widget.On()

    def _set_annotated_cube_actor_labels(self, labels):
        aca = self._annotated_cube_actor
        aca.SetXMinusFaceText(labels[0])
        aca.SetXPlusFaceText(labels[1])
        aca.SetYMinusFaceText(labels[2])
        aca.SetYPlusFaceText(labels[3])
        aca.SetZMinusFaceText(labels[4])
        aca.SetZPlusFaceText(labels[5])

###########################################################################
def vtkmip_copy(src, dst):
    """Given two vtkMedicalImageProperties instances, copy all
    attributes from the one to the other.

    Rather use vtkMedicalImageProperties.DeepCopy.
    """

    import module_kits.vtk_kit as vk
    mip_kw = vk.constants.medical_image_properties_keywords

    for kw in mip_kw:
        # get method objects for the getter and the setter
        gmo = getattr(src, 'Get%s' % (kw,))
        smo = getattr(dst, 'Set%s' % (kw,))
        # from the get to the set!
        smo(gmo())
        

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

