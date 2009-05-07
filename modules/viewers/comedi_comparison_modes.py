# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

import comedi_utils
reload(comedi_utils)
import vtk


###########################################################################
# 2D:
# * vtkRectilinearWipeWidget, de-emphasize anything outside focus:
#   yellow blue inside, grey outside
# * IPW with yellow-blue difference inside focus, grey data1 outside
# 3D:
# * context gray (silhouette, data1), focus animated
# * context gray (silhouette, data2), focus difference image

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

