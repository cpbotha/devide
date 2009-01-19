from module_base import ModuleBase
from module_mixins import IntrospectModuleMixin
import module_utils

HTML_START = '<html><body>'
HTML_END = '</body></html>'

def render_actions(lines):
    return '<p><b>%s</b>' % ('<br>'.join(lines),)

class QuickInfo(IntrospectModuleMixin, ModuleBase):

    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        self._input = None

        self._view_frame = None
        self._create_view_frame()
        self.view()

        self.view_initialised = True

    def _create_view_frame(self):
        import resources.python.quick_info_frames
        reload(resources.python.quick_info_frames)

        self._view_frame = module_utils.instantiate_module_view_frame(
                self, self._module_manager,
                resources.python.quick_info_frames.QuickInfoFrame)

        module_utils.create_standard_object_introspection(
                self, self._view_frame,
                self._view_frame.view_frame_panel,
                {'Module (self)' : self})

        module_utils.create_eoca_buttons(self, self._view_frame,
                                        self._view_frame.view_frame_panel)


    def close(self):
        for i in range(len(self.get_input_descriptions())):
            self.set_input(i, None)
        
        self._view_frame.Destroy()
        del self._view_frame

        ModuleBase.close(self)

    def get_input_descriptions(self):
        return ('Any DeVIDE data',)

    def get_output_descriptions(self):
        return ()

    def set_input(self, idx, input_stream):
        self._input = input_stream

    def get_output(self, idx):
        raise RuntimeError

    def logic_to_config(self):
        pass

    def config_to_logic(self):
        pass

    def view_to_config(self):
        pass

    def config_to_view(self):
        pass

    def view(self):
        self._view_frame.Show()
        self._view_frame.Raise()

    def execute_module(self):
        oh = self._view_frame.output_html
        ip = self._input
       
        if ip is None:
            html = 'There is no input (input is "None").'

        elif self.check_vtk(ip):
            html = self.analyse_vtk(ip)
        elif self.check_itk(ip, txt):
            html = self.analyse_itk(ip)
        else:
            html = 'Could not determine type of data.'

        oh.SetPage(html)


    def analyse_vtk(self, ip):
        lines = [HTML_START]
        # main data type
        lines.append("<h2>%s</h2>" % (ip.GetClassName(),))

        if ip.IsA('vtkPolyData'):
            # more detailed human-readable description
            lines.append('<p>VTK format polygonal / mesh data<br>')
            lines.append('%d points<br>' % (ip.GetNumberOfPoints(),))
            lines.append('%d polygons<br>' % (ip.GetNumberOfPolys(),))
            # how can the data be visualised
            lines.append('<p><b>Surface render with slice3dVWR.</b>')
        elif ip.IsA('vtkImageData'):
            # more detailed human-readable description
            lines.append('<p>VTK format regular grid / volume<br>')
            dx,dy,dz = ip.GetDimensions()
            lines.append('%d x %d x %d == %d voxels<br>' % \
                    (dx,dy,dz,dx*dy*dz))
            lines.append('physical spacing %.2f x %.2f x %.2f<br>' % \
                    ip.GetSpacing())
            # how can the data be visualised
            lines.append(render_actions(
                ["Slice through the data (MPR) with 'slice3dVWR'",
                "Extract an isosurface with 'contour'",
                "Direct volume render (DVR) with 'VolumeRender'"]
                ))

        elif ip.IsA('vtkImplicitFunction'):
            # more detailed human-readable description
            lines.append('<p>VTK format implicit function')
            # possible actions
            lines.append(
                    """<p><b>Clip mesh data with 'clipPolyData'<br>
                    Sample to volume with 'ImplicitToVolume'</b>""")

        elif ip.IsA('vtkProp'):
            # more detailed human-readable description
            lines.append('<p>VTK object in 3-D scene')
            # possible actions
            lines.append(
                    render_actions(
                    ["Visualise in 3-D scene with 'slice3dVWR'"])
                    )



        # give information about point (geometry) attributes
        try:
            pd = ip.GetPointData()
        except AttributeError:
            pass
        else:
            na = pd.GetNumberOfArrays()
            if na > 0:
                lines.append('<p>Data associated with points:<br>')

                for i in range(na):
                    a = pd.GetArray(i)
                    l = "'%s': %d %d-element tuples of type %s<br>" % \
                            (a.GetName(), a.GetNumberOfTuples(),
                            a.GetNumberOfComponents(),
                            a.GetDataTypeAsString())
                    lines.append(l)


        lines.append(HTML_END)
        return '\n'.join(lines)

    def check_vtk(self, ip):
        try:
            cn = ip.GetClassName()
        except AttributeError:
            return False
        else:
            if cn.startswith('vtk'):
                return True

        return False


    def analyse_itk(self, ip):
        return "ITK Object"

    def check_itk(self, ip, txt):
        return False

        


