from gen_mixins import SubjectMixin
import geometry
from moduleBase import moduleBase
from moduleMixins import introspectModuleMixin
import moduleUtils
import Measure2DFrame
reload(Measure2DFrame)

import vtk
import vtktudoss
import wx

class M2DMeasurementInfo:
    pass

class M2DWidget:
    """Class for encapsulating widget binding and all its metadata.
    """

    def __init__(self, widget, name, type_string):
        """
        @param type_string: ellipse
        """
        self.widget = widget
        self.name = name
        self.type_string = type_string
        self.measurement_string = ""
        # we'll use this to pack all widget-specific measurement
        # information
        self.measurement_info = M2DMeasurementInfo()


class M2DWidgetList:
    """List of M2DWidgets that can be queried by name or type.
    """

    def __init__(self):
        self._wdict = {}

    def close(self):
        pass

    def add(self, widget):
        """widget is an instance of M2DWidget.
        """

        if not widget.name:
            raise KeyError("Widget has to have a name.")

        if widget.name in self._wdict:
            raise KeyError("Widget with that name already in list.")

        self._wdict[widget.name] = widget


    def get_names(self):
        return self._wdict.keys()

    def get_widget(self, name):
        return self._wdict[name]

    def get_widgets_of_type(self, type_string):
        """Return a list of all widgets of type type_string.
        """

        wlist = []
        for wname, w in self._wdict.items():
            if w.type_string == type_string:
                wlist.append(w)

        return wlist

    def remove(self, name):
        """Remove widget with name from internal dict.
        Return binding to widget that was just removed (so that client
        can do widget specific finalisation.
        """

        w = self._wdict[name]
        del(self._wdict[name])
        
        
        return w
    
    def rename_widget(self, old_name, new_name):
        """After profuse error-checking, rename widget with old_name
        to new_name.
        """

        if not new_name:
            raise KeyError('Widget cannot have empty name.')

        if old_name not in self._wdict:
            raise KeyError('widget %s not in list.' % (old_name,))

        if new_name in self._wdict:
            raise KeyError('widget with name %s alread exists.' %
                    (new_name,))

        w = self.get_widget(old_name)
        self.remove(old_name)
        w.name = new_name
        self.add(w)
        

    def __contains__(self, name):
        """Returns true if there's a widget with that name already in
        the list.
        """

        return name in self._wdict

class Measure2D(introspectModuleMixin, moduleBase):
    def __init__(self, module_manager):
        moduleBase.__init__(self, module_manager)

        self._view_frame = None
        self._viewer = None
        self._input_image = None
        self._dummy_image_source = vtk.vtkImageMandelbrotSource()
        
        self._widgets = M2DWidgetList()

        # build frame
        self._view_frame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager, Measure2DFrame.Measure2DFrame)

        # now link up all event handlers
        self._bind_events()

        # then build VTK pipeline
        self._create_vtk_pipeline()

        # set us up with dummy input
        self._setup_new_image()

        # show everything
        self.view()

        
    def close(self):
        if self._view_frame is not None:
            # with this complicated de-init, we make sure that VTK is 
            # properly taken care of
            self._viewer.GetRenderer().RemoveAllViewProps()
            self._viewer.SetupInteractor(None)
            self._viewer.SetRenderer(None)
            # this finalize makes sure we don't get any strange X
            # errors when we kill the module.
            self._viewer.GetRenderWindow().Finalize()
            self._viewer.SetRenderWindow(None)
            self._viewer.DebugOn()
            del self._viewer
            # done with VTK de-init

            self._view_frame.close()
            
    def view(self):
        self._view_frame.Show()
        self._view_frame.Raise()

        # GOTCHA!! (finally)
        # we need to do this to make sure that the Show() and Raise() above
        # are actually performed.  Not doing this is what resulted in the
        # "empty renderwindow" bug after module reloading, and also in the
        # fact that shortly after module creation dummy data rendered outside
        # the module frame.
        # YEAH.
        wx.SafeYield()

        self.render()

        # so if we bring up the view after having executed the network once,
        # re-executing will not do a set_input()!  (the scheduler doesn't
        # know that the module is now dirty)  Two solutions:
        # * make module dirty when view is activated
        # * activate view at instantiation. <--- we're doing this now.
        
    def get_input_descriptions(self):
        return ('Image data',)

    def get_output_descriptions(self):
        return ('self', 'widget_list')

    def get_output(self, idx):
        if idx == 0:
            return self
        else:
            return self._widgets

    def execute_module(self):
        self.render()

    def logic_to_config(self):
        pass

    def config_to_logic(self):
        pass
    
    def set_input(self, idx, input_stream):
        if self._input_image != input_stream:
            self._input_image = input_stream
            self._setup_new_image()
            
    def _bind_events(self):
        """Setup all event handling based on the view frame.
        """
                
        slice_slider = self._view_frame._image_control_panel.slider
        slice_slider.Bind(wx.EVT_SLIDER, self._handler_slice_slider)
        
        new_measurement_button = \
            self._view_frame._measurement_panel.create_button
        new_measurement_button.Bind(wx.EVT_BUTTON, self._handler_new_measurement_button)

        rb = self._view_frame._measurement_panel.rename_button
        rb.Bind(wx.EVT_BUTTON,
                self._handler_rename_measurement_button)

        db = self._view_frame._measurement_panel.delete_button
        db.Bind(wx.EVT_BUTTON,
                self._handler_delete_measurement_button)

        eb = self._view_frame._measurement_panel.enable_button
        eb.Bind(wx.EVT_BUTTON,
                self._handler_enable_measurement_button)

        db = self._view_frame._measurement_panel.disable_button
        db.Bind(wx.EVT_BUTTON,
                self._handler_disable_measurement_button)

    def _create_vtk_pipeline(self):
        """Create pipeline for viewing 2D image data.
        
        """
        if self._viewer is None and not self._view_frame is None:
            
            if True:
                self._viewer = vtk.vtkImageViewer2()
                self._viewer.SetupInteractor(self._view_frame._rwi)
                self._viewer.GetRenderer().SetBackground(0.3,0.3,0.3)
                
            else:
                ren = vtk.vtkRenderer()
                self._view_frame._rwi.GetRenderWindow().AddRenderer(ren)

    def _get_selected_measurement_names(self):
        """Return list of names of selected measurement widgets.
        """
    
        grid = self._view_frame._measurement_panel.measurement_grid
        sr = grid.GetSelectedRows()

        return [grid.GetCellValue(idx,0) for idx in sr]

    def _handler_enable_measurement_button(self, event):

        snames = self._get_selected_measurement_names()
        for sname in snames:
            w = self._widgets.get_widget(sname)
            print "about to enable ", w.name
            w.widget.SetEnabled(1)

        self.render()



    def _handler_disable_measurement_button(self, event):
      
        snames = self._get_selected_measurement_names()
        for sname in snames:
            w = self._widgets.get_widget(sname)
            print "about to disable ", w.name
            w.widget.SetEnabled(0)

        self.render()

    def _handler_rename_measurement_button(self, event):
        # FIXME: abstract method that returns list of names of
        # selected measurement widgets

        grid = self._view_frame._measurement_panel.measurement_grid
        
        # returns list of selected row indices, we're only going to
        # rename the first one
        sr = grid.GetSelectedRows()

        if not sr:
            return

        idx = sr[0]
        name = grid.GetCellValue(idx, 0)
    
        new_name = wx.GetTextFromUser(
            'Enter a new name for this measurement.',
            'Rename Module',
            name)

        if new_name:
            w = self._widgets.get_widget(name)
            self._widgets.rename_widget(name, new_name)
            self._sync_measurement_grid()

    def _handler_delete_measurement_button(self, event):
        grid = self._view_frame._measurement_panel.measurement_grid

        sr = grid.GetSelectedRows()

        if not sr:
            return

        for idx in sr:
            name = grid.GetCellValue(idx, 0)

            w = self._widgets.get_widget(name)
            w.widget.SetEnabled(0)
            w.widget.SetInteractor(None)

            self._widgets.remove(name)

        self._sync_measurement_grid()

    def _handler_new_measurement_button(self, event):
        
        widget_type = 0


        if widget_type == 0:

            # instantiate widget with correct init vars
            name = self._view_frame._measurement_panel.name_cb.GetValue()
            if not name or name in self._widgets:
                # FIXME: add error message here
                pass
            else:

                w = vtktudoss.vtkEllipseWidget()
                w.SetInteractor(self._view_frame._rwi)
                w.SetEnabled(1)
                

                widget = M2DWidget(w, name, 'ellipse')
                # add it to the internal list
                self._widgets.add(widget)

                def observer_interaction(o, e):
                    r = o.GetRepresentation()
                    s = r.GetLabelText()
                    widget.measurement_string = s 
                    # c, axis_lengths, radius_vectors
                    mi = widget.measurement_info
                    mi.c = [0.0,0.0,0.0]
                    r.GetCenterWorldPosition(mi.c)
                    mi.c[2] = 0.0
                    mi.axis_lengths = (
                        r.GetSemiMajorAxisLength() * 2.0,
                        r.GetSemiMinorAxisLength() * 2.0,
                        0.0)
                    mi.radius_vectors = (
                            [0.0,0.0,0.0],
                            [0.0,0.0,0.0],
                            [0.0,0.0,0.0])
                    r.GetSemiMajorAxisVector(mi.radius_vectors[0])
                    r.GetSemiMinorAxisVector(mi.radius_vectors[1])

                    self._sync_measurement_grid()

                # make sure state is initialised  (if one just places
                # the widget without interacting, the observer won't
                # be invoked and measurement_info won't have the
                # necessary attributes; if the network then executes,
                # there will be errors)
                widget.measurement_string = ''
                mi = widget.measurement_info
                mi.c = [0.0,0.0,0.0]
                mi.axis_lengths = (0.0, 0.0, 0.0)
                mi.radius_vectors = (
                        [0.0,0.0,0.0],
                        [0.0,0.0,0.0],
                        [0.0,0.0,0.0])

                w.AddObserver('EndInteractionEvent',
                              observer_interaction)

                # and then make the display thing sync up
                self._sync_measurement_grid()
        
        else:
            handle = vtk.vtkPointHandleRepresentation2D()
            handle.GetProperty().SetColor(1,0,0)

            rep = vtk.vtkDistanceRepresentation2D()
            rep.SetHandleRepresentation(handle)
            rep.GetAxis().SetNumberOfMinorTicks(4)
            rep.GetAxis().SetTickLength(9)
            rep.GetAxis().SetTitlePosition(0.2)
        
            w = vtk.vtkDistanceWidget()
            w.SetInteractor(self._view_frame._rwi)        
            #w.CreateDefaultRepresentation()
            w.SetRepresentation(rep)
        
            w.SetEnabled(1)

            # instantiate widget with correct init vars
            widget = M2DWidget(w, 'name', 'ellipse')
            # add it to the internal list
            self._widgets.add(w)

        self.render()
            
    def _handler_slice_slider(self, event):
        if not self._input_image is None:
            val = self._view_frame._image_control_panel.slider.GetValue()
            self._viewer.SetSlice(val)

    def render(self):
        self._view_frame._rwi.Render()
                
    def _setup_new_image(self):
        """Based on the current self._input_image and the viewer, this thing
        will make sure that we reset to some usable default.
        """

        if not self._viewer is None:
            if not self._input_image is None:
                self._viewer.SetInput(self._input_image)
            else:
                self._viewer.SetInput(self._dummy_image_source.GetOutput())

            ii = self._viewer.GetInput()
            
            ii.UpdateInformation()
            ii.Update()
            range = ii.GetScalarRange()
            self._viewer.SetColorWindow(range[1] - range[0])
            self._viewer.SetColorLevel(0.5 * (range[1] + range[0]))
            
            icp = self._view_frame._image_control_panel
            icp.slider.SetRange(self._viewer.GetSliceMin(),
                                self._viewer.GetSliceMax())
            icp.slider.SetValue(self._viewer.GetSliceMin())
            
            #self._viewer.UpdateDisplayExtent()
            self._viewer.GetRenderer().ResetCamera()


    def _sync_measurement_grid(self):
        """Synchronise measurement grid with internal list of widgets.
        """

        # for now we just nuke the whole thing and redo everything

        grid = self._view_frame._measurement_panel.measurement_grid
        if grid.GetNumberRows() > 0:
            grid.DeleteRows(0, grid.GetNumberRows())

        wname_list = self._widgets.get_names()
        wname_list.sort()
        for wname in wname_list:
            w = self._widgets.get_widget(wname)
            grid.AppendRows()   
            cur_row = grid.GetNumberRows() - 1
            grid.SetCellValue(cur_row, 0, w.name)
            grid.SetCellValue(cur_row, 1, w.type_string)
            grid.SetCellValue(cur_row, 2, w.measurement_string)

        # in general when we sync, the module is dirty, so we should
        # flag this in the module manager.  when the user sees this
        # and schedules an execute, the scheduler will execute us and
        # all parts of the network that are dependent on us.
        self._moduleManager.modify_module(self)

