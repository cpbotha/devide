from module_base import ModuleBase
from module_mixins import IntrospectModuleMixin
import module_utils
import operator

HTML_START = '<html><body>'
HTML_END = '</body></html>'

def render_actions(lines):
    ms = '<p><b><ul>%s</ul></b></p>'
    # this should yield: <li>thing 1\n<li>thing 2\n<li>thing 3 etc
    bullets = '\n'.join(['<li>%s</li>' % l for l in lines])
    return ms % (bullets,)

    #return '<p><b>%s</b>' % ('<br>'.join(lines),)

def render_description(lines):
    return '<p>%s' % ('<br>'.join(lines),)

def render_main_type(line):
    return '<h2>%s</h2>' % (line,)

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
        elif self.check_itk(ip):
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
        lines = [HTML_START]
        noc = ip.GetNameOfClass()
        mt = 'itk::%s' % (noc,)
        lines.append(render_main_type(mt))


        if noc == 'Image':
            # general description ##################################
            from module_kits.misc_kit.misc_utils import \
                    get_itk_img_type_and_dim
            itype, dim, vector = get_itk_img_type_and_dim(ip)
            dim = int(dim)

            if vector:
                vs = 'vector'
            else:
                vs = 'scalar'

            dl = ['ITK format %d-dimensional %s %s image / volume' % \
                    (dim, itype, vs)]

            s = ip.GetLargestPossibleRegion().GetSize()
            dims = [s.GetElement(i) for i in range(dim)]
            # this results in 234 x 234 x 123 x 123 (depending on num
            # of dimensions)
            dstr = ' x '.join(['%s'] * dim) % tuple(dims)
            # the reduce multiplies all dims with each other
            dl.append('%s = %d pixels' % \
                    (dstr, reduce(operator.mul, dims)))
            comps = ip.GetNumberOfComponentsPerPixel() 
            dl.append('%d component(s) per pixel' % (comps,))
            # spacing string
            spacing = [ip.GetSpacing().GetElement(i) 
                    for i in range(dim)]
            sstr = ' x '.join(['%.2f'] * dim) % tuple(spacing)
            dl.append('physical spacing %s' % (sstr,))

            lines.append(render_description(dl))


            # possible actions ######################################
            al = ["Process with other ITK filters", 
                    "Convert to VTK with ITKtoVTK"]
            lines.append(render_actions(al))



        lines.append(HTML_END)
        return '\n'.join(lines)

    def check_itk(self, ip):
        if repr(ip).startswith('<C itk::'):
            return True
        else:
            return False

        


