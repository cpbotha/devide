# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

import comedi_utils
reload(comedi_utils)
import vtk
import vtktudoss
from module_kits import vtk_kit


###########################################################################
# 2D:
# * vtkRectilinearWipeWidget, de-emphasize anything outside focus:
#   yellow blue inside, grey outside
# * IPW with yellow-blue difference inside focus, grey data1 outside
# * gradient of data2 overlaid on data1
# * two colour channels, for scalar and for gradient combination (you
#   should be able to do this wiht pre-proc, colourise data BEFORE)
# 3D:
# * context gray (silhouette, data1), focus animated
# * context gray (silhouette, data2), focus difference image

###########################################################################
class ComparisonMode:
    def __init__(self, comedi, cfg_dict):
        pass

    def set_inputs(self, data1, data2, data2m, distance):
        pass

    def update_vis(self):
        """If all inputs are available, update the visualisation.

        This also has to be called if there is no valid registered
        output anymore so that the view can be disabled.
        """
        pass

###########################################################################
class CheckerboardCM(ComparisonMode):
    """Comparison mode that shows a checkerboard of the two matched
    datasets.
    """

    def __init__(self, comedi, cfg_dict):
        self._comedi = comedi
        self._cfg = cfg_dict
        
        rwi,ren = comedi.get_compvis_vtk()
        self._sv = comedi_utils.CMSliceViewer(rwi, ren)
        comedi.sync_slice_viewers.add_slice_viewer(self._sv)

        self._cb = vtk.vtkImageCheckerboard()

        # we'll store our local bindings here
        self._d1 = None
        self._d2m = None

    def close(self):
        self._comedi.sync_slice_viewers.remove_slice_viewer(self._sv)
        self._sv.close()
        # disconnect the checkerboard
        self._cb.SetInput1(None)
        self._cb.SetInput2(None)

    def update_vis(self):
        # if there's valid data, do the vis man!
        d2m = self._comedi.get_data2m()
        d1 = self._comedi.get_data1()

        new_data = False

        if d1 != self._d1:
            self._d1 = d1
            self._cb.SetInput1(d1)
            new_data = True

        if d2m != self._d2m:
            self._d2m = d2m
            self._cb.SetInput2(d2m)
            new_data = True

        if new_data:
            # this means the situation has changed
            if d1 and d2m:
                # we have two datasets and can checkerboard them
                # enable the slice viewer
                self._sv.set_input(self._cb.GetOutput())
                # sync it to data1
                sv1 = self._comedi._data1_slice_viewer
                self._comedi.sync_slice_viewers.sync_all(
                        sv1, [self._sv])

            else:
                # this means one of our datasets is NULL
                # disable the slice viewer
                self._sv.set_input(None)

        # now check for UI things
        cp = self._comedi._view_frame.pane_controls.window
        divx = cp.cm_checkerboard_divx.GetValue()
        divy = cp.cm_checkerboard_divy.GetValue()
        divz = cp.cm_checkerboard_divz.GetValue()

        ndiv = self._cb.GetNumberOfDivisions()
        if ndiv != (divx, divy, divz):
            self._cb.SetNumberOfDivisions((divx, divy, divz))



        # we do render to update the 3D view
        self._sv.render()

###########################################################################
class Data2MCM(ComparisonMode):
    """Match mode that only displays the matched data2.
    """

    def __init__(self, comedi, cfg_dict):
        self._comedi = comedi
        self._cfg = cfg_dict

        rwi,ren = comedi.get_compvis_vtk()
        self._sv = comedi_utils.CMSliceViewer(rwi, ren)
        comedi.sync_slice_viewers.add_slice_viewer(self._sv)

    def close(self):
        self._comedi.sync_slice_viewers.remove_slice_viewer(self._sv)
        self._sv.close()

    def update_vis(self):
        # if there's valid data, do the vis man!
        o = self._comedi.match_mode.get_output()

        # get current input
        ci = self._sv.get_input()

        if o != ci:
            # new data!  do something!
            self._sv.set_input(o)

            # if it's not null, sync with primary viewer
            if o is not None:
                sv1 = self._comedi._data1_slice_viewer
                self._comedi.sync_slice_viewers.sync_all(
                        sv1, [self._sv])


        # we do render to update the 3D view
        self._sv.render()

class FocusDiffCM(ComparisonMode):
    """Match mode that displays difference between data in focus area
    with blue/yellow colour scale, normal greyscale for the context.
    """

    def __init__(self, comedi, cfg_dict):
        self._comedi = comedi
        self._cfg = cfg_dict

        # color scales thingy
        self._color_scales = vtk_kit.color_scales.ColorScales()

        # instantiate us a slice viewer
        rwi,ren = comedi.get_compvis_vtk()
        self._sv = comedi_utils.CMSliceViewer(rwi, ren)
        # now make our own MapToColors
        lut = self._sv.ipws[0].GetLookupTable()
        m2c = vtktudoss.vtkCVImageMapToColors()
        #m2c = vtk.vtkImageMapToColors()
        m2c.SetLookupTable(lut)
        self._sv.ipws[0].SetColorMap(m2c)
        comedi.sync_slice_viewers.add_slice_viewer(self._sv)

        # now build up the VTK pipeline #############################
        # we'll use these to scale data between 0 and max.
        self._ss1 = vtk.vtkImageShiftScale()
        self._ss1.SetOutputScalarTypeToShort()
        self._ss2 = vtk.vtkImageShiftScale()
        self._ss2.SetOutputScalarTypeToShort()
        # then something to subtract the two
        self._sub = vtk.vtkImageMathematics()
        self._sub.SetOperationToSubtract()
        self._sub.SetInput1(self._ss1.GetOutput())
        self._sub.SetInput2(self._ss2.GetOutput())

        # we have to cast the confidence to shorts as well
        self._ssc = vtk.vtkImageShiftScale()
        self._ssc.SetOutputScalarTypeToShort()

        self._iac = vtk.vtkImageAppendComponents()
        # data1 will form the context
        self._iac.SetInput(0, self._ss1.GetOutput())
        # subtraction will form the focus
        self._iac.SetInput(1, self._sub.GetOutput())
        # third input will be the confidence
        self._iac.SetInput(2, self._ssc.GetOutput())


        # we'll store our local bindings here
        self._d1 = None
        self._d2m = None
        self._conf = None

    def close(self):
        self._comedi.sync_slice_viewers.remove_slice_viewer(self._sv)
        self._sv.close()

        # take care of all our bindings to VTK classes
        del self._ss1
        del self._ss2
        del self._sub

    def update_vis(self):
        # if there's valid data, do the vis man!
        d2m = self._comedi.get_data2m()
        d1 = self._comedi.get_data1()
        conf = self._comedi.match_mode.get_confidence()

        new_data = False

        if d1 != self._d1:
            self._d1 = d1
            self._ss1.SetInput(d1)
            new_data = True

        if d2m != self._d2m:
            self._d2m = d2m
            self._ss2.SetInput(d2m)
            new_data = True

        if conf != self._conf:
            self._conf = conf
            self._ssc.SetInput(self._conf)

        if new_data:
            if d1 and d2m and conf:
                self._sub.Update()
                r = self._sub.GetOutput().GetScalarRange()
                #lut = self._color_scales.LUT_Linear_BlueToYellow(r)
                lut = self._color_scales.LUT_BlueToYellow(r)
                self._sv.ipws[0].GetColorMap().SetLookupTable2(lut)

                print "about to update iac"
                self._iac.SetNumberOfThreads(1)
                self._iac.Update()
                print "done updating iac"

                self._sv.set_input(self._iac.GetOutput())

                # sync it to data1
                sv1 = self._comedi._data1_slice_viewer
                self._comedi.sync_slice_viewers.sync_all(
                        sv1, [self._sv])

            else:
                self._sv.set_input(None)

        # we do render to update the 3D view
        self._sv.render()

