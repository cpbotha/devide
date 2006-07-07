import code
import sys
import wx

class PythonShellMixin:

    def _open_python_file(self):
        fd = wx.FileDialog(
            self._view_frame,
            'Select file to open into current edit',
            wildcard='*.py', style=wx.OPEN)

        if fd.ShowModal() == wx.ID_OK:
            filename = fd.GetPath()
            
            f = open(filename, 'r')
                
            t = f.read()
            # replace stupid DOS CR/LF with newline
            t = t.replace('\r\n', '\n')
            # any CRs that are left are nuked
            t = t.replace('\r', '')

            f.close()
                
            return filename, t

        else:
            return (None, None)

    def _save_python_file(self, text):
        fd = wx.FileDialog(
            self._view_frame,
            'Select filename to save current edit to',
            wildcard='*.py', style=wx.SAVE)

        if fd.ShowModal() == wx.ID_OK:
            filename = fd.GetPath()
            
            f = open(filename, 'w')
            f.write(text)
            f.close()

            return filename
        
        return None
                
    def _run_source(self, text, shell_window):
        """Compile and run the source given in text in the shell interpreter's
        local namespace.

        The idiot pyshell goes through the whole shell.push -> interp.push
        -> interp.runsource -> InteractiveInterpreter.runsource hardcoding the
        'mode' parameter (effectively) to 'single', thus breaking multi-line
        definitions and whatnot.

        Here we do some deep magic (ha ha) to externally override the interp
        runsource.  Python does completely rule.
        """

        text = text.replace('\r\n', '\n')
        text = text.replace('\r', '\n')
        
        interp = shell_window.interp
        stdin, stdout, stderr = sys.stdin, sys.stdout, sys.stderr
        sys.stdin, sys.stdout, sys.stderr = \
                   interp.stdin, interp.stdout, interp.stderr

        # look: calling class method with interp instance as first parameter
        # comes down to the same as interp calling runsource() as its
        # parent method.
        more = code.InteractiveInterpreter.runsource(
            interp, text, '<input>', 'exec')

        # make sure the user can type again
        shell_window.prompt()

        sys.stdin = stdin
        sys.stdout = stdout
        sys.stderr = stderr

        return more
    
    def support_vtk(self):
        if hasattr(self, 'vtk_renderwindows'):
            return

        import module_kits
        if 'vtk_kit' not in module_kits.module_kit_list:
            self.output_text('No VTK support.')
            return
        
        from module_kits import vtk_kit
        vtk = vtk_kit.vtk

        def get_render_info(instance_name):
            instance = self._moduleManager.get_instance(instance_name)

            if instance is None:
                return None
            
            class RenderInfo:
                pass

            render_info = RenderInfo()

            render_info.renderer = instance.get_3d_renderer()
            render_info.render_window = instance.get_3d_render_window()
            render_info.interactor = instance.\
                                     get_3d_render_window_interactor()
            

            return render_info

        new_dict = {'vtk' : vtk,
                    'vtk_get_render_info' : get_render_info}

        self.interp.locals.update(new_dict)
        self.__dict__.update(new_dict)

        self.output_text('VTK support loaded.')

    def support_matplotlib(self):
        if hasattr(self, 'mpl_figure_handles'):
            return

        import module_kits

        if 'matplotlib_kit' not in module_kits.module_kit_list:
            self.output_text('No matplotlib support.')
            return

        from module_kits import matplotlib_kit
        pylab = matplotlib_kit.pylab
        
        # setup shutdown logic ########################################
        self.mpl_figure_handles = []

        def mpl_close_handler():
            for fh in self.mpl_figure_handles:
                pylab.close(fh)
        
        self.close_handlers.append(mpl_close_handler)
        
        # hook our mpl_new_figure method ##############################

        # mpl_new_figure hook so that all created figures are registered
        # and will be closed when the module is closed
        def mpl_new_figure(*args):
            handle = pylab.figure(*args)
            self.mpl_figure_handles.append(handle)
            return handle

        def mpl_close_figure(handle):
            """Close matplotlib figure.
            """
            pylab.close(handle)
            if handle in self.mpl_figure_handles:
                idx = self.mpl_figure_handles(handle)
                del self.mpl_figure_handles[idx]

        # replace our hook's documentation with the 'real' documentation
        mpl_new_figure.__doc__ = pylab.figure.__doc__

        # stuff the required symbols into the module's namespace ######
        new_dict = {'matplotlib' : matplotlib_kit.matplotlib,
                    'pylab' : matplotlib_kit.pylab,
                    'mpl_new_figure' : mpl_new_figure,
                    'mpl_close_figure' : mpl_close_figure}
        
        self.interp.locals.update(new_dict)
        self.__dict__.update(new_dict)

        self.output_text('matplotlib support loaded.')

