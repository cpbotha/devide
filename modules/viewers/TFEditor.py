# - make our own window control for colour-sequence bar
# - this should also have separate (?) line with HSV colour vertices
# - on this line, there should be vertical lines indicating the current
#   position of all the opacity transfer function vertices
# - abstract floatcanvas-derived linear function editor into wx_kit

import os
from module_base import ModuleBase
from module_mixins import IntrospectModuleMixin,\
        FileOpenDialogModuleMixin
import module_utils
from external import transfer_function_widget
import vtk
import wx


TF_LIBRARY = {
        'CT Hip (bones+vasculature)' : [
            (-1024.0, (0, 0, 0), 0), 
            (184.65573770491801, (255, 128, 128), 0.0), 
            (225.20534629404619, (255, 128, 128), 0.73857868020304562), 
            (304.8359659781288, (255, 128, 128), 0.0), 
            (377.70491803278696, (233, 231, 148), 0.0), 
            (379.48967193195631, (233, 231, 148), 1.0), 
            (3072.0, (255, 255, 255), 1)],
        'CT Hip (test)' : [
            (-1024.0, (0, 0, 0), 0),
            (117.50819672131138, (255, 128, 128), 0.0),
            (595.93442622950829, (255, 255, 255), 1.0), 
            (3072.0, (255, 255, 255), 1)],
        'Panoramix (prototype)' : [
            (-1024.0, (0, 0, 0), 0), 
            (136.33994334277622, (214, 115, 115), 0.0), 
            (159.5467422096317, (230, 99, 99), 0.24788732394366197), 
            (200.1586402266289, (255, 128, 128), 0.0), 
            (252.37393767705385, (206, 206, 61), 0.40000000000000002), 
            (287.18413597733706, (255, 128, 128), 0.0), 
            (403.21813031161469, (206, 61, 67), 0.13521126760563384), 
            (525.05382436260629, (255, 255, 255), 0.0), 
            (612.07932011331445, (255, 255, 255), 0.92957746478873238), 
            (3072.0, (255, 255, 255), 1)] 
        }

class TFEditor(IntrospectModuleMixin, FileOpenDialogModuleMixin, ModuleBase):

    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        self._volume_input = None

        self._opacity_tf = vtk.vtkPiecewiseFunction()
        self._colour_tf = vtk.vtkColorTransferFunction()
        self._lut = vtk.vtkLookupTable()

        # list of tuples, where each tuple (scalar_value, (r,g,b,a))
        self._config.transfer_function = [
                (0, (0,0,0), 0),
                (255, (255,255,255), 1)
                ]

        self._view_frame = None
        self._create_view_frame()
        self._bind_events()

        self.view()

        # all modules should toggle this once they have shown their
        # stuff.
        self.view_initialised = True

        self.config_to_logic()
        self.logic_to_config()
        self.config_to_view()


    def _bind_events(self):

        def handler_blaat(event):
            tf_widget = event.GetEventObject() # the tf_widget
            ret = tf_widget.get_current_point_info()
            if not ret is None:
                val, col, opacity = ret
                vf = self._view_frame
                vf.colour_button.SetBackgroundColour(col)
                vf.cur_scalar_text.SetValue('%.2f' % (val,))
                vf.cur_col_text.SetValue(str(col))
                vf.cur_opacity_text.SetValue('%.2f' % (opacity,))

        vf = self._view_frame
        tfw = vf.tf_widget
        tfw.Bind(transfer_function_widget.EVT_CUR_PT_CHANGED,
                handler_blaat)

        def handler_colour_button(event):
            coldialog = wx.ColourDialog(vf, tfw.colour_data)

            if coldialog.ShowModal() == wx.ID_OK:
                colour = coldialog.GetColourData().GetColour().Get()
                tfw.colour_data = coldialog.GetColourData()

                tfw.set_current_point_colour(colour)

        vf.colour_button.Bind(wx.EVT_BUTTON, handler_colour_button)

        def handler_delete_button(event):
            tfw.delete_current_point()

        vf.delete_button.Bind(wx.EVT_BUTTON, handler_delete_button)

        def handler_auto_range_button(event):
            try:
                range = self._volume_input.GetScalarRange()
            except AttributeError:
                self._module_manager.log_error(
                        'Could not determine range from input. ' +
                        'Have you connected some input data and ' +
                        'has the network executed at least once?')
            else:
                vf = self._view_frame
                vf.scalar_min_text.SetValue(str(range[0]))
                vf.scalar_max_text.SetValue(str(range[1]))

        vf.auto_range_button.Bind(wx.EVT_BUTTON,
                handler_auto_range_button)


        def handler_apply_range_button(event):
            try:
                min = float(vf.scalar_min_text.GetValue())
                max = float(vf.scalar_max_text.GetValue())
            except ValueError:
                self._module_manager.log_error(
                'Invalid scalar MIN / MAX.')

            else:
                tfw.set_min_max(min, max)

        vf.apply_range_button.Bind(wx.EVT_BUTTON,
                handler_apply_range_button)


        def handler_load_preset_button(event):
            key = vf.preset_choice.GetStringSelection()
            preset_tf = TF_LIBRARY[key]
            tfw.set_transfer_function(preset_tf)

        vf.load_preset_button.Bind(wx.EVT_BUTTON,
                handler_load_preset_button)

        def handler_file_save_button(event):
            filename = self.filename_browse(self._view_frame, 
            'Select DVTF filename to save to', 
            'DeVIDE Transfer Function (*.dvtf)|*.dvtf|All files (*)|*', 
            style=wx.SAVE)

            if filename:
                # if the user has NOT specified any fileextension, we
                # add .dvtf.  (on Win this gets added by the
                # FileSelector automatically, on Linux it doesn't)
                if os.path.splitext(filename)[1] == '':
                    filename = '%s.dvtf' % (filename,)

                self._save_tf_to_file(filename)

        vf.file_save_button.Bind(wx.EVT_BUTTON,
                handler_file_save_button)

        def handler_file_load_button(event):
            filename = self.filename_browse(self._view_frame, 
            'Select DVTF filename to load', 
            'DeVIDE Transfer Function (*.dvtf)|*.dvtf|All files (*)|*', 
            style=wx.OPEN)

            if filename:
                self._load_tf_from_file(filename)

        vf.file_load_button.Bind(wx.EVT_BUTTON,
                handler_file_load_button)


        # auto_range_button
        

    def _create_view_frame(self):
        import resources.python.tfeditorframe
        reload(resources.python.tfeditorframe)

        self._view_frame = module_utils.instantiate_module_view_frame(
            self, self._module_manager,
            resources.python.tfeditorframe.TFEditorFrame)

        module_utils.create_standard_object_introspection(
            self, self._view_frame, self._view_frame.view_frame_panel,
            {'Module (self)' : self})

        # add the ECASH buttons
        module_utils.create_eoca_buttons(self, self._view_frame,
                                        self._view_frame.view_frame_panel)

        # and customize the presets choice
        vf = self._view_frame
        keys = TF_LIBRARY.keys()
        keys.sort()
        vf.preset_choice.Clear()
        for key in keys:
            vf.preset_choice.Append(key)

        vf.preset_choice.Select(0)




    def close(self):
        for i in range(len(self.get_input_descriptions())):
            self.set_input(i, None)
        
        self._view_frame.Destroy()
        del self._view_frame

        ModuleBase.close(self)

    def get_input_descriptions(self):
        return ('Optional input volume',)

    def get_output_descriptions(self):
        return ('VTK Opacity Transfer Function',
                'VTK Colour Transfer Function',
                'VTK Lookup Table')

    def set_input(self, idx, input_stream):
        self._volume_input = input_stream

    def get_output(self, idx):
        if idx == 0:
            return self._opacity_tf
        elif idx == 1:
            return self._colour_tf
        else:
            return self._lut

    def logic_to_config(self):
        pass

    def config_to_logic(self):
        self._opacity_tf.RemoveAllPoints()
        self._colour_tf.RemoveAllPoints()

        for p in self._config.transfer_function:
            self._opacity_tf.AddPoint(p[0], p[2])
            r,g,b = [i / 255.0 for i in p[1]]
            self._colour_tf.AddRGBPoint(
                    p[0],r,g,b)

        lut_res = 1024 
        minmax = self._view_frame.tf_widget.get_min_max()
        self._lut.SetTableRange(minmax)
        self._lut.SetNumberOfTableValues(lut_res)

        # lut_res - 1: lut_res points == lut_res-1 intervals
        incr = (minmax[1] - minmax[0]) / float(lut_res - 1)
        for i in range(lut_res):
            v = minmax[0] + i * incr
            rgb = self._colour_tf.GetColor(v)
            o = self._opacity_tf.GetValue(v)
            self._lut.SetTableValue(i, rgb + (o,))

    def view_to_config(self):
        self._config.transfer_function = \
                self._view_frame.tf_widget.get_transfer_function()

    def config_to_view(self):
        vf = self._view_frame
        tfw = vf.tf_widget
        tfw.set_transfer_function(
                self._config.transfer_function)
        min,max = tfw.get_min_max()
        vf.scalar_min_text.SetValue('%.1f' % (min,))
        vf.scalar_max_text.SetValue('%.1f' % (max,))

    def view(self):
        self._view_frame.Show()
        self._view_frame.Raise()

    def execute_module(self):
        pass

    def _load_tf_from_file(self, filename):
        try:
            loadf = file(filename, 'r')
            tf = eval(loadf.read(), {"__builtins__": {}})
            loadf.close()

        except Exception, e:
            self._module_manager.log_error_with_exception(
                    'Could not load transfer function: %s.' %
                    (str(e),))

        else:
            self._view_frame.tf_widget.set_transfer_function(
                    tf)
        
    def _save_tf_to_file(self, filename):
        tf = self._view_frame.tf_widget.get_transfer_function()

        try:
            savef = file(filename, 'w')
            savef.write("# DeVIDE Transfer Function DVTF v1.0\n%s" % \
                    (str(tf),))
            savef.close()
        except Exception, e:
            self._module_manager.log_error(
                    'Error saving transfer function: %s.' % (str(e),))

        else:
            self._module_manager.log_message(
                    'Saved %s.' % (filename,))
        

