from module_base import module_base
import vtk
import vtkpython
from vtkPipeline.vtkPipeline import \
     vtkPipelineBrowser, vtkPipelineSegmentBrowser

class vtk_mc_flt(module_base):
    def __init__(self):
	self.mc = vtkpython.vtkMarchingCubes()
        self.mc.SetProgressMethod(lambda s=self, po=self.mc:
                                  s.vtk_progress_callback(po))

        #self.isovalue = Tkinter.StringVar()

        self.config_window = None
        #self.create_view_window()

    def close(self):
        # take care of that view_window
        self.config_window.destroy()
	# check that self.mc isn't deleted yet
        if dir(self).count('mc'):
	    del self.mc

    def apply_config(self):
        self.mc.SetValue(0, float(self.isovalue.get()))

    def create_view_window(self, parent_window=None):
        """Create configuration/view window.

        This method sets up the config window and immediately hides it.  When
        the user wants to view/config, the window is simply de-iconised.
        """
	self.config_window = Tkinter.Toplevel(parent_window)
	self.config_window.title("vtk_mc_flt.py configuration")
	self.config_window.protocol ("WM_DELETE_WINDOW",
                                     self.config_window.withdraw)


        iso_entry = Pmw.EntryField(self.config_window,
                                   labelpos = 'w',
                                   value = '55.5',
                                   label_text = 'Isovalue:',
                                   validate = {'validator' : 'real'},
                                   entry_textvariable=self.isovalue)
        iso_entry.grid(row=0,column=0)
        #iso_entry.pack(side=TOP)
        
	
	# button box
	box = Pmw.ButtonBox(self.config_window)
	box.add('vtkMarchingCubes', command=lambda self=self,
                pw=parent_window: self.configure_vtk_object(self.mc, pw))
	box.add('pipeline', text='Pipeline', command=lambda self=self,
                pw=parent_window, vtk_objs=(self.mc):
                self.browse_vtk_pipeline(vtk_objs, pw))
	box.grid(row=1, column=0, columnspan=1, sticky=W+E)
        #box.pack(side=TOP)
        box.alignbuttons()

        self.add_CSAEO_box(self.config_window, 2, 1)
        
        self.config_window.withdraw()

    def execute_module(self):
        self.mc.Update()
	
    def get_input_descriptions(self):
	return ('vtkStructuredPoints',)
    
    def set_input(self, idx, input_stream):
	self.mc.SetInput(input_stream)
    
    def get_output_descriptions(self):
	return (self.mc.GetOutput().GetClassName(),)

    def get_output(self, idx):
	return self.mc.GetOutput()

    def sync_config(self):
        # for now we act as if we have one isovalue
        self.isovalue.set(self.mc.GetValue(0))

    def view(self, parent_window=None):
        self.sync_config()
        self.config_window.deiconify()
        
