# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

from external.ObjectListView import ColumnDefn, EVT_CELL_EDIT_FINISHING
import itk
from module_kits import itk_kit
import module_utils
import vtk
import wx

###########################################################################
class MatchMode:
    """Plugin class that takes care of the Match Mode UI panel,
    interaction for indicating matching structures, and the subsequent
    registration.
    """

    def __init__(self, comedi, config_dict):
        raise NotImplementedError

    def close(self):
        """De-init everything.

        it's important that you de-init everything (including event
        bindings) as close() is called many times during normal
        application use.  Each time the user changes the match mode
        tab, the previous match mode is completely de-initialised.
        """
        raise NotImplementedError

    def get_output(self):
        """Return the transformed data2.  Returns None if this is not
        possible, due to the lack of input data for example.  Call
        after having called transform.
        """
        raise NotImplementedError

    def get_confidence(self):
        """Return confidence field, usually a form of distance field
        to the matching structures.
        """

        raise NotImplementedError

    def transform(self):
        """After calling this method, the output will be available and
        ready.
        """
        raise NotImplementedError

###########################################################################
class Landmark:
    def __init__(self, name, index_pos, world_pos, ren):
        # we'll use this to create new actors.
        self.ren = ren

        self._create_actors()

        self.set_name(name)
        self.set_world_pos(world_pos)
        self.set_index_pos(index_pos)
       
    def close(self):
        self.ren.RemoveViewProp(self.c3da)
        self.ren.RemoveViewProp(self.ca)

    def _create_actors(self):

        # 1. create really small 3D cursor to place at relevant point
        d = 2 # 2 mm dimension 
        cs = vtk.vtkCursor3D()
        cs.AllOff()
        cs.AxesOn()
        cs.SetModelBounds(-d, +d, -d, +d, -d, +d)
        cs.SetFocalPoint(0,0,0)

        m = vtk.vtkPolyDataMapper()
        m.SetInput(cs.GetOutput())

        self.c3da = vtk.vtkActor()
        self.c3da.SetPickable(0)
        self.c3da.SetMapper(m)

        self.ren.AddActor(self.c3da)

        # 2. create caption actor with label
        ca = vtk.vtkCaptionActor2D()
        ca.GetProperty().SetColor(1,1,0)
        tp = ca.GetCaptionTextProperty()
        tp.SetColor(1,1,0)
        tp.ShadowOff()
        ca.SetPickable(0)
        ca.SetAttachmentPoint(0,0,0) # we'll move this later
        ca.SetPosition(25,10)
        ca.BorderOff()
        ca.SetWidth(0.3)
        ca.SetHeight(0.04)

        # this will be changed at the first property set
        ca.SetCaption('.')

        self.ca = ca
        self.ren.AddActor(ca)


    def get_world_pos_str(self):
        return '%.2f, %.2f, %.2f' % tuple(self.world_pos)

    def get_world_pos(self):
        return self._world_pos

    def set_world_pos(self, world_pos):
        self.c3da.SetPosition(world_pos)
        self.ca.SetAttachmentPoint(world_pos)

        self._world_pos = world_pos

    # why have I not been doing this forever?
    # - because these properties get clobbered real easy.  *sigh*
    world_pos = property(get_world_pos, set_world_pos)

    def get_name(self):
        """Test doc string!
        """
        return self._name

    def set_name(self, name):
        self.ca.SetCaption(name)
        self._name = name

    name = property(get_name, set_name)

    def get_index_pos(self):
        return self._index_pos

    def set_index_pos(self, index_pos):
        self._index_pos = index_pos[0:3]

    index_pos = property(get_index_pos, set_index_pos)


###########################################################################
class LandmarkList:
    """List of landmarks that also maintains a config dictionary.
    """

    def __init__(self, config_dict, olv, ren):
        """
        @param config_list: list that we will fill with (name,
        world_pos) tuples.
        @param olv: ObjectListView that will be configured to handle
        the UI to the list.
        """

        self._config_dict = config_dict
        self.landmark_dict = {}
        self._olv = olv
        self._ren = ren

        # there we go, sync internal state to passed config
        for name,(index_pos, world_pos) in config_dict.items():
            self.add_landmark(index_pos, world_pos, name)

        olv.Bind(EVT_CELL_EDIT_FINISHING,
                self._handler_olv_edit_finishing)

        # if you don't set valueSetter, this thing overwrites my
        # pretty property!!
        olv.SetColumns([
            ColumnDefn("Name", "left", 50, "name",
            valueSetter=self.olv_setter),
            ColumnDefn("Position", "left", 200, "get_world_pos_str",
                isSpaceFilling=True, isEditable=False)])

        olv.SetObjects(self.olv_landmark_list)

    def add_landmark(self, index_pos, world_pos, name=None):
        if name is None:
            name = str(len(self.landmark_dict))

        lm = Landmark(name, index_pos, world_pos, self._ren)
        self.landmark_dict[lm.name] = lm
        # set the config_dict.  cheap operation, so we do the whole
        # thing every time.
        self.update_config_dict()
        # then update the olv
        self._olv.SetObjects(self.olv_landmark_list)

    def close(self):
        self._olv.Unbind(EVT_CELL_EDIT_FINISHING)
        [lm.close() for lm in self.landmark_dict.values()]

    def _get_olv_landmark_list(self):
        """Returns list of Landmark objects, sorted by name.  This is
        given to the ObjectListView.
        """
        ld = self.landmark_dict
        keys,values = ld.keys(),ld.values()
        keys.sort()
        return [ld[key] for key in keys]

    olv_landmark_list = property(_get_olv_landmark_list)

    def get_index_pos_list(self):
        """Retuns a list of 3-element discrete coordinates for the
        current landmarks, sorted by name.
        """

        ld = self.landmark_dict
        keys = ld.keys()
        keys.sort()
        return [ld[key].index_pos for key in keys]

    def _handler_olv_edit_finishing(self, evt):
        """This can get called only for "name" column edits, nothing
        else.
        """
        if evt.cellValue == evt.rowModel.name:
            # we don't care, name stays the same
            return

        if len(evt.cellValue) > 0 and \
                evt.cellValue not in self.landmark_dict:
                    # unique value, go ahead and change
                    # our olv_setter will be called at the right
                    # moment
                    return

        # else we veto this change
        # message box?!
        evt.Veto()

    def olv_setter(self, lm_object, new_name):
        # delete the old binding from the dictionary
        del self.landmark_dict[lm_object.name]
        # change the name in the object
        # ARGH!  why does this setting clobber the property?!
        #lm_object.name = new_name
        lm_object.set_name(new_name)
        # insert it at its correct spot
        self.landmark_dict[new_name] = lm_object
        # update the config dict
        self.update_config_dict()

    def remove_landmarks(self, names_list):
        for name in names_list:
            # get the landmark
            lm = self.landmark_dict[name]
            # de-init the landmark
            lm.close()
            # remove it from the dictionary
            del self.landmark_dict[name]

        # finally update the config dictionary
        self.update_config_dict()
        # then tell the olv about the changed situation
        self._olv.SetObjects(self.olv_landmark_list)

    def move_landmark(self, name, index_pos, world_pos):
        lm = self.landmark_dict[name]
        #lm.world_pos = world_pos
        lm.set_index_pos(index_pos)
        lm.set_world_pos(world_pos)
        self.update_config_dict()
        self._olv.SetObjects(self.olv_landmark_list)

    def update_config_dict(self):
        # re-init the whole thing; note that we don't re-assign, that
        # would just bind to a new dictionary and not modify the
        # passed one.
        self._config_dict.clear()
        for key,value in self.landmark_dict.items():
            self._config_dict[key] = value.index_pos, value.world_pos


###########################################################################

KEY_DATA1_LANDMARKS = 'data1_landmarks'
KEY_DATA2_LANDMARKS = 'data2_landmarks'
KEY_MAX_DISTANCE = 'max_distance'

class SStructLandmarksMM(MatchMode):
    """Class representing simple landmark-transform between two sets
    of points.
    """

    # API methods #####
    def __init__(self, comedi, config_dict):
        """
        @param comedi: Instance of comedi that will be used to update
        GUI and views.
        @param config_dict: This dict, part of the main module config,
        will be kept up to date throughout.
        """
        
        self._comedi = comedi
        self._cfg = config_dict

        # if we get an empty config dict, configure!
        if 'data1_landmarks' not in self._cfg:
            self._cfg['data1_landmarks'] = {}

        # do the list
        cp = comedi._view_frame.pane_controls.window
        r1 = comedi._data1_slice_viewer.renderer
        self._data1_landmarks = \
                LandmarkList(
                        self._cfg['data1_landmarks'], 
                        cp.data1_landmarks_olv, r1)

        if 'data2_landmarks' not in self._cfg:
            self._cfg['data2_landmarks'] = {}


        r2 = comedi._data2_slice_viewer.renderer
        self._data2_landmarks = \
                LandmarkList(
                        self._cfg['data2_landmarks'],
                        cp.data2_landmarks_olv, r2)

        self._setup_ui()
        self._bind_events()

        # we'll use this to store a binding to the current output
        self._output = None
        # and this to store a binding to the current confidence
        self._confidence = None

        # remember, this turns out to be the transform itself
        self._landmark = vtk.vtkLandmarkTransform()
        # and this guy is going to do the work
        self._trfm = vtk.vtkImageReslice()
        self._trfm.SetInterpolationModeToLinear()
        # setup a progress message:
        module_utils.setup_vtk_object_progress(
                self._comedi, self._trfm,
                'Transforming Data 2')


        # distance field will be calculated up to this distance,
        # saving you time and money!
        if KEY_MAX_DISTANCE not in self._cfg:
            self._cfg[KEY_MAX_DISTANCE] = 43

        md = self._cfg[KEY_MAX_DISTANCE]

        # use itk fast marching to generate confidence field
        self._fm = itk.FastMarchingImageFilter.IF3IF3.New()
        self._fm.SetStoppingValue(md)
        self._fm.SetSpeedConstant(1.0)
        # setup a progress message
        itk_kit.utils.setup_itk_object_progress(
            self, self._fm, 'itkFastMarchingImageFilter',
            'Propagating confidence front.', None,
            comedi._module_manager)


        # and a threshold to clip off the really high values that fast
        # marching inserts after its max distance
        self._thresh = t = itk.ThresholdImageFilter.IF3.New()
        t.SetOutsideValue(md)
        # values equal to or greater than this are set to outside value
        t.ThresholdAbove(md)
        itk_kit.utils.setup_itk_object_progress(
                self, self._thresh, 'itkThresholdImageFilter',
                'Clipping high values in confidence field.', None,
                comedi._module_manager)

        t.SetInput(self._fm.GetOutput())

        # and a little something to convert it back to VTK world
        self._itk2vtk = itk.ImageToVTKImageFilter.IF3.New()
        self._itk2vtk.SetInput(t.GetOutput())

    def close(self):
        self._data1_landmarks.close()
        self._data2_landmarks.close()
        self._unbind_events()

        # get rid of the transform
        self._trfm.SetInput(None)
        del self._trfm

        # nuke landmark
        del self._landmark

        # nuke fastmarching
        del self._fm
        del self._thresh

    def get_confidence(self):
        return self._confidence

    def get_output(self):
        return self._output

    def transform(self):
        """If we have valid data and a valid set of matching
        landmarks, transform data2.

        Even if nothing has changed, this WILL perform the actual
        transformation, so don't call this method unnecessarily.
        """

        d1i = self._comedi._data1_slice_viewer.get_input()
        d2i = self._comedi._data2_slice_viewer.get_input()

        if d1i and d2i:
            # we force the landmark to do its thing
            try:
                self._transfer_landmarks_to_vtk()
            except RuntimeError, e:
                # could not transfer points
                self._output = None
                # tell the user why
                self._comedi._module_manager.log_error(
                        str(e))
            else:
                # points are set, update the transformation
                self._landmark.Update()
                # reslice transform transforms the sampling grid. 
                self._trfm.SetResliceTransform(self._landmark.GetInverse())
                self._trfm.SetInput(d2i)
                self._trfm.SetInformationInput(d1i)
                self._trfm.Update()
                self._output = self._trfm.GetOutput()

                # then calculate distance field #####################
                c2vc = itk_kit.utils.coordinates_to_vector_container
                lm = self._data1_landmarks
                seeds = c2vc(lm.get_index_pos_list(), 0)
                self._fm.SetTrialPoints(seeds)
                # now make sure the output has exactly the right
                # dimensions and everyfink
                o = d1i.GetOrigin()
                s = d1i.GetSpacing()
                d = d1i.GetDimensions()
                we = d1i.GetWholeExtent()

                fmo = itk.Point.D3()
                for i,e in enumerate(o):
                    fmo.SetElement(i,e)

                fms = itk.Vector.D3()
                for i,e in enumerate(s):
                    fms.SetElement(i,e)

                fmr = itk.ImageRegion._3()
                fmsz = fmr.GetSize()
                fmi = fmr.GetIndex()
                for i,e in enumerate(d):
                    fmsz.SetElement(i,e)
                    # aaah! so that's what the index is for! :)
                    # some VTK volumes have a 0,0,0 origin, but their
                    # whole extent does not begin at 0,0,0.  For
                    # example the output of a vtkExtractVOI does this.
                    fmi.SetElement(i, we[2*i])
                
                self._fm.SetOutputOrigin(fmo)
                self._fm.SetOutputSpacing(fms)
                self._fm.SetOutputRegion(fmr)

                # drag the whole thing through the vtk2itk converter
                self._itk2vtk.Update()
                self._confidence = self._itk2vtk.GetOutput()

        else:
            # not enough valid inputs, so no data.
            self._output = None
            # also disconnect the transform, so we don't keep data
            # hanging around
            self._trfm.SetInput(None)

            #
            self._confidence = None

    # PRIVATE methods #####
    def _add_data1_landmark(self, index_pos, world_pos, name=None):
        self._data1_landmarks.add_landmark(index_pos, world_pos)

    def _add_data2_landmark(self, index_pos, world_pos, name=None):
        self._data2_landmarks.add_landmark(index_pos, world_pos)

    def _bind_events(self):
        # remember to UNBIND all of these in _unbind_events!


        vf = self._comedi._view_frame
        cp = vf.pane_controls.window

        # bind to the add button
        cp.lm_add_button.Bind(wx.EVT_BUTTON, self._handler_add_button)


        cp.data1_landmarks_olv.Bind(
                wx.EVT_LIST_ITEM_RIGHT_CLICK,
                self._handler_solv_right_click)

        cp.data2_landmarks_olv.Bind(
                wx.EVT_LIST_ITEM_RIGHT_CLICK,
                self._handler_tolv_right_click)

    def _handler_add_button(self, e):
        cp = self._comedi._view_frame.pane_controls.window
        v = cp.cursor_text.GetValue()
        if v.startswith('d1'):
            ip = self._comedi._data1_slice_viewer.current_index_pos
            wp = self._comedi._data1_slice_viewer.current_world_pos
            self._add_data1_landmark(ip, wp)
        elif v.startswith('d2'):
            ip = self._comedi._data2_slice_viewer.current_index_pos
            wp = self._comedi._data2_slice_viewer.current_world_pos
            self._add_data2_landmark(ip, wp)

    def _handler_delete_selected_lms(self, evt, i):
        cp = self._comedi._view_frame.pane_controls.window
        if i == 0:
            olv = cp.data1_landmarks_olv
            dobjs = olv.GetSelectedObjects()
            self._data1_landmarks.remove_landmarks(
                    [o.name for o in dobjs])
        else:
            olv = cp.data2_landmarks_olv
            dobjs = olv.GetSelectedObjects()
            self._data2_landmarks.remove_landmarks(
                    [o.name for o in dobjs])

    def _handler_move_selected_lm(self, evt, i):
        cp = self._comedi._view_frame.pane_controls.window
        v = cp.cursor_text.GetValue()
        if v.startswith('d1') and i == 0:
            # get the current world position
            ip = self._comedi._data1_slice_viewer.current_index_pos
            wp = self._comedi._data1_slice_viewer.current_world_pos
            # get the currently selected object
            olv = cp.data1_landmarks_olv
            mobjs = olv.GetSelectedObjects()
            if mobjs:
                mobj = mobjs[0]
                # now move...
                self._data1_landmarks.move_landmark(mobj.name, ip, wp)
                
        elif v.startswith('d2') and i == 1:
            # get the current world position
            ip = self._comedi._data2_slice_viewer.current_index_pos
            wp = self._comedi._data2_slice_viewer.current_world_pos
            # get the currently selected object
            olv = cp.data2_landmarks_olv
            mobjs = olv.GetSelectedObjects()
            if mobjs:
                mobj = mobjs[0]
                # now move...
                self._data2_landmarks.move_landmark(mobj.name, ip, wp)

    def _handler_solv_right_click(self, evt):
        olv = evt.GetEventObject()

        # popup that menu
        olv.PopupMenu(self._solv_menu, evt.GetPosition())

    def _handler_tolv_right_click(self, evt):
        olv = evt.GetEventObject()

        # popup that menu
        olv.PopupMenu(self._tolv_menu, evt.GetPosition())

    def _setup_ui(self):
        """Do some UI-specific setup.
        """

        vf = self._comedi._view_frame

        self._solv_menu = wx.Menu('Landmarks context menu')
        self._tolv_menu = wx.Menu('Landmarks context menu')

        # i = [0,1] for data1 and data2 landmarks respectively
        for i,m in enumerate([self._solv_menu, self._tolv_menu]):
            # move landmarks
            id_move_landmark = wx.NewId()
            m.Append(id_move_landmark,
                    "Move first selected",
                    "Move first selected landmark to current cursor.")

            vf.Bind(wx.EVT_MENU,
                    lambda e, i=i:
                    self._handler_move_selected_lm(e,i),
                    id = id_move_landmark)

            # deletion of landmarks
            id_delete_landmark = wx.NewId()
            m.Append(id_delete_landmark,
                    "Delete selected",
                    "Delete all selected landmarks.")

            vf.Bind(wx.EVT_MENU, 
                lambda e, i=i: self._handler_delete_selected_lms(e,i),
                id = id_delete_landmark)
        


    def _transfer_landmarks_to_vtk(self):
        """Copy landmarks from internal vars to sets of vtkPoints,
        then set on our landmark transform filter.
        """
       
        sld = self._data1_landmarks.landmark_dict
        tld = self._data2_landmarks.landmark_dict

        names = sld.keys()

        sposs, tposs = [],[]
        for name in names:
            sposs.append(sld[name].world_pos)
            try:
                tposs.append(tld[name].world_pos)
            except KeyError:
                raise RuntimeError(
                        'Could not find data2 landmark with name %s.'
                        % (name,))

        # now transfer the two lists to vtkPoint lists
        # SOURCE:
        data1_points = vtk.vtkPoints()
        data1_points.SetNumberOfPoints(len(sposs))
        for idx,pt in enumerate(sposs):
            data1_points.SetPoint(idx, pt)


        # TARGET:
        data2_points = vtk.vtkPoints()
        data2_points.SetNumberOfPoints(len(tposs))
        for idx,pt in enumerate(tposs):
            data2_points.SetPoint(idx, pt)

        # we want to map data2 onto data1
        self._landmark.SetSourceLandmarks(data2_points)
        self._landmark.SetTargetLandmarks(data1_points)
       
    def _unbind_events(self):
        vf = self._comedi._view_frame
        cp = vf.pane_controls.window

        # bind to the add button
        cp.lm_add_button.Unbind(wx.EVT_BUTTON)

        cp.data1_landmarks_olv.Unbind(
                wx.EVT_LIST_ITEM_RIGHT_CLICK)

        cp.data2_landmarks_olv.Unbind(
                wx.EVT_LIST_ITEM_RIGHT_CLICK)

