#!/usr/bin/env python
#
# $Id: ConfigVtkObj.py,v 1.3 2002/04/29 16:57:42 cpbotha Exp $
#
# This python program/module takes a VTK object and provides a GUI 
# configuration for it.
#
# Copyright (C) 2000 Prabhu Ramachandran
# Conversion to wxPython copyright (c) 2002 Charl P. Botha
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
# 
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA  02111-1307, USA.
#
# Author contact information:
#   Prabhu Ramachandran <prabhu_r@users.sf.net>
#   http://www.aero.iitm.ernet.in/~prabhu/
#
#   Charl P. Botha <cpbotha@ieee.org>
#   http://cpbotha.net/

""" This program/module takes a VTK object and provides a GUI
configuration for it.  Right now Tkinter is used for the GUI.

note by cpbotha:
Actually, I've gone and changed it to wxPython.  I was a bit lazy,
so I've actually nuked the tk bits instead of nicely adding the
wxPython as option.  I think that the author (ha ha) could perhaps
get wonders done with a contextual diff. :)

"""

import vtkMethodParser
import types, string, re

try:
    from wxPython.wx import *
except ImportError:
    print "Cannot import the wxPython.wx module. Install it and try again."
    sys.exit (1)

#print_info = tkMessageBox.showinfo

def print_err (msg):
    # create nice formatted string with tracebacks and all
    dmsg = \
         string.join(traceback.format_exception(sys.exc_type,
                                                sys.exc_value,
                                                sys.exc_traceback))
    wxLogError(dmsg)
    wxLogError(msg)
    wxLog_FlushActive()

# use this to print stuff for the user command run from the GUI
def prn (x):
    print x

def tk_2_vtk_color (tk_col):
    "Converts a Tk RGB color to a VTK RGB color."
    ONE_255 = 1.0/255.0
    return (tk_col[0]*ONE_255, tk_col[1]*ONE_255, tk_col[2]*ONE_255)


class VtkShowDoc:
    
    """ This class displays the documentation included in the __doc__
    attribute of the VTK object and its methods."""

    def __init__ (self, parent_frame=None):
        self._parent_frame = parent_frame
        
    def check_obj (self):
        try:
            self.obj.GetClassName ()
        except AttributeError:            
            msg = "Sorry! The object passed does not seem to be a "\
                  "VTK object!!"
            print_err (msg)
            return 0
        try:
            doc_ = self.obj.__doc__
        except AttributeError:
            msg = "Sorry! This particular version of the VTK-Python "\
                  "bindings does not feature embedded documentation "\
                  "of the class and its methods.  Please use a more "\
                  "up to date version of VTK."
            print_err (msg)
            return 0
        else:
            return 1

    def show_doc (self, vtk_obj):
        self.obj = vtk_obj
        if self.check_obj ():
            self.setup ()
            self.add_doc ()

    def setup (self):
        self._frame = wxFrame(parent = self._parent_frame, id=-1,
                              title='Class Documentation for %s' %
                              self.obj.GetClassName ())
        EVT_CLOSE(self._frame, lambda e, s=self: s.quit)

        # make panel that will contain htmlwindow and close button
        panel = wxPanel(parent=self._frame, id=-1)

        # then the html window
        self._html_window = wxHtmlWindow(parent=panel, id=-1)

        close_id = wxNewId()
        close_button = wxButton(parent=panel, id=close_id, label="Close")

        top_sizer = wxBoxSizer(wxVERTICAL)
        top_sizer.Add(self._html_window, option=1, flag=wxEXPAND)
        top_sizer.Add(close_button, option=0, flag=wxALIGN_CENTER_HORIZONTAL)

        panel.SetAutoLayout(true)
        panel.SetSizer(top_sizer)
        top_sizer.Fit(self._frame)
        top_sizer.SetSizeHints(self._frame)

	#self.root.bind ("<Alt-c>", self.quit)
            
        #self.txt.tag_config ("heading", foreground="blue",
        #                     underline=1, justify='center')
        #self.txt.tag_config ("subheading", foreground="blue",
        #                     underline=1, justify='left')
        #self.txt.tag_config ("item", underline=1, justify='left')
        #self.txt.tag_config ("data", wrap='word')
    
    def add_doc (self):
        data_ = self.obj.GetClassName ()

        the_html = "<h1>Class Documentation for %s</h1><br><br>" % data_

        the_html = the_html + \
                   string.join(string.split(self.obj.__doc__, '\n'), '<br>')
        the_html = the_html + '<br><br>' + \
                   "Please note that all the documented methods are not "\
                   "configurable using the GUI provided.<br><br><br>"\
                   "<h2>Class method documentation</h2><br><br>"

        for i in dir (self.obj):
            if i == '__class__':
                continue
            try:
                data_ = eval ("self.obj.%s.__doc__"%i)
            except AttributeError:
                pass
            else:
                the_html = the_html + \
                           "<h3>%s</h3><br>" + \
                           string.join(string.split(data_,'\n'),'<br') + \
                           "<br><br>"

    def quit (self, event=None):
        self._frame.Destroy()


class ConfigVtkObj:

    """ This class finds the methods for a given vtkObject and creates
    a GUI to configure the object.  It uses the output from the
    VtkMethodParser class. """

    def __init__ (self, renwin=None):
	# This variable is used to do a redraw on changing the objects
	# properties.
	self.renwin = renwin
	self.parser = vtkMethodParser.VtkMethodParser ()
	self.state_patn = re.compile ("To[A-Z0-9]")
        self.update_meth = None

    def set_render_window (self, renwin):
	self.renwin = renwin

    def set_update_method (self, method):
        """ This sets a method that the instance will call when any
        changes are made."""
        self.update_meth = method

    def parse_methods (self, vtk_obj):
	self.parser.parse_methods (vtk_obj)
	self.toggle_meths = self.parser.toggle_methods ()
	self.state_meths = self.parser.state_methods ()
	self.get_set_meths = self.parser.get_set_methods ()
	self.get_meths = self.parser.get_methods ()

    def get_state (self, meths):
        end = self.state_patn.search (meths[0]).start ()
        get_m = 'G'+meths[0][1:end]
        orig = eval ("self.vtk_obj.%s()"%get_m)
        for i in range (len(meths)):
            m = meths[i]
            eval ("self.vtk_obj.%s()"%m)
            val = eval ("self.vtk_obj.%s()"%get_m)
            if val == orig:
                break
        return i

    def configure(self, parent_frame, vtk_obj):
	"Configure the vtk_object passed."
	self.vtk_obj = vtk_obj
        self.vtk_warn = -1
        try:
            self.vtk_warn = vtk_obj.GetGlobalWarningDisplay ()
        except AttributeError:
            pass
        else:
            vtk_obj.GlobalWarningDisplayOff ()
	self.parse_methods (vtk_obj)
	self.make_gui (parent_frame)
        if self.vtk_warn > -1:
            self.vtk_obj.SetGlobalWarningDisplay (self.vtk_warn)

    def make_gui (self, parent_window):
	"Makes the configuration GUI."

        # the top level frame
        self._frame = wxFrame(parent=parent_window, id=-1,
                              title="Configure %s"%
                              self.vtk_obj.GetClassName ())
        EVT_CLOSE(self._frame, lambda e, s=self: s.cancel)

        # then the panel which we'll populate
        panel = wxPanel(parent=self._frame, id=-1)

        # first with a vertical sizer, settings at the top, buttons
        # + controls at the bottom
        top_sizer = wxBoxSizer(wxVERTICAL)

        self._notebook = wxNotebook(parent=panel, id=-1,
                                    size=(640,480))
        nbsizer = wxNotebookSizer(self._notebook)

        top_sizer.Add(nbsizer, option=1, flag=wxEXPAND)

	#frame = Tkinter.Frame (self.root)
	#frame.pack (side='top', expand=1, fill='both')
	#left = Tkinter.Frame (frame)
	#left.grid (row=0, column=0, sticky='nw')
	#right = Tkinter.Frame (frame)
	#right.grid (row=0, column=1, sticky='nw')

	self.make_gui_vars ()

	top_sizer.Add(self.make_control_gui(panel), option=0, flag=wxEXPAND)
        
	self._notebook.AddPage(self.make_toggle_gui(self._notebook), 'Toggles')
        self._notebook.AddPage(self.make_state_gui(self._notebook), 'States')
        #self._notebook.AddPage(self.make_get_gui(self._notebook), 'Gets')
        self._notebook.AddPage(self.make_get_set_gui(self._notebook),
                               'Get-Set')

        panel.SetAutoLayout(true)
        panel.SetSizer(top_sizer)
        top_sizer.Fit(self._frame)
        top_sizer.SetSizeHints(self._frame)

        self._frame.Show(true)

    def make_gui_vars (self):
	"Create the various variables used for the GUI."
	#self.user_command = Tkinter.StringVar ()
	self.toggle_var = [-1 for i in self.toggle_meths]
        self.state_var = [-1 for i in self.state_meths]
        self.get_set_var = ["" for i in self.get_set_meths]
        self.get_set_texts = [None for i in self.get_set_var]


	#self.get_set_var = []
	#for i in range (0, len (self.get_set_meths)):
	#    self.get_set_var.append (Tkinter.StringVar ())
	#    self.get_set_var[i].set ("")

	#self.get_lab = []
	#for i in range (0, len (self.get_meths)):
	#    self.get_lab.append (None)

    def make_control_gui (self, parent):
        """Makes all the control GUI elements.

        This will create the control buttons and the command line
        interface bit.  All the controls must be children of the parameter
        parent.  This method must return a sizer that can be added to the
        top level sizer.
        """
        vert_sizer = wxBoxSizer(wxVERTICAL)
        command_sizer = wxBoxSizer(wxHORIZONTAL)
        button_sizer = wxBoxSizer(wxHORIZONTAL)
        vert_sizer.Add(command_sizer, option=0, flag=wxEXPAND)
        vert_sizer.Add(button_sizer, option=0, flag=wxEXPAND)

        # the button that will show a little help dialog...
        command_help_id = wxNewId()
        command_button = wxButton(parent, id=command_help_id, label="Help")
        # just defaults for the button, we just want its default size
        command_sizer.Add(command_button)
        EVT_BUTTON(parent, command_help_id, lambda e, s=self: s.help_user())

        
        command_entry_id = wxNewId()
        command_entry = wxTextCtrl(parent, id=command_entry_id)
        command_sizer.Add(command_entry, option=1, flag=wxEXPAND)
        EVT_TEXT_ENTER(parent, command_entry_id,
                       lambda e, s=self: s.run_command())

        classdoc_id = wxNewId()
        classdoc_button = wxButton(parent, id=classdoc_id,
                                   label="Class Documentation")
        button_sizer.Add(classdoc_button)
        EVT_BUTTON(parent, classdoc_id, lambda e, s=self: s.show_doc())

        update_id = wxNewId()
        update_button = wxButton(parent, id=update_id,
                                 label="Update")
        button_sizer.Add(update_button)
        EVT_BUTTON(parent, update_id, lambda e, s=self: s.update_gui())
        
        apply_id = wxNewId()
        apply_button = wxButton(parent, id=apply_id,
                                 label="Apply")
        button_sizer.Add(apply_button)
        EVT_BUTTON(parent, apply_id, lambda e, s=self: s.apply_changes())

        ok_button = wxButton(parent, wxID_OK, label="OK")
        button_sizer.Add(ok_button)
        EVT_BUTTON(parent, wxID_OK, lambda e, s=self: s.ok_done())

        cancel_button = wxButton(parent, wxID_CANCEL, label="Cancel")
        button_sizer.Add(cancel_button)
        EVT_BUTTON(parent, wxID_CANCEL, lambda e, s=self: s.cancel())

        return vert_sizer

    def make_toggle_gui (self, parent):
	"""Create the toggle methods.

        This method should do whatever it does into a panel that it creates.
        This panel should be returned, as it's going to be stuffed in a
        notebook, typically the parent.  Remember that the panel should be
        child to the parent.
        """
        panel = wxPanel(parent, id=-1)
        vert_sizer = wxBoxSizer(wxVERTICAL)
        panel.SetAutoLayout(true)
        panel.SetSizer(vert_sizer)
        
	n_meth = len (self.toggle_meths)
	for i in range (0, n_meth):
	    m = "Get"+self.toggle_meths[i][:-2]
	    self.toggle_var[i] = eval ("self.vtk_obj.%s ()"%m)
            cb_id = wxNewId()
            cb = wxCheckBox(parent=panel, id=cb_id, label=self.toggle_meths[i])
            cb.SetValue(self.toggle_var[i])
            EVT_CHECKBOX(panel, cb_id,
                         lambda event, s=self, i=i: s.toggle_cb(event, i))
            vert_sizer.Add(cb, option=0, flag=wxEXPAND)

        return panel

    def toggle_cb(self, event, i):
        """Event handler to simulate tk's groovy active variables.

        When the user clicks a checkbox, this callback gets triggered and
        modifies our internal variable.  Neat.
        """
        self.toggle_var[i] = event.GetEventObject().GetValue()
	    
    def make_state_gui (self, parent):
	"Create the state methods.  (SetAToB methods)"
        panel = wxPanel(parent, id=-1)
        vert_sizer = wxBoxSizer(wxVERTICAL)
        panel.SetAutoLayout(true)
        panel.SetSizer(vert_sizer)
        
	n_meth = len (self.state_meths)
	rw = 0
	for i in range (0, n_meth):
	    meths = self.state_meths[i]
            self.state_var[i] = self.get_state (meths)

            # these 2 lines ripped from get_state
            end = self.state_patn.search (meths[0]).start ()
            get_m = 'G'+meths[0][1:end]
            
            rb_id = wxNewId()
            rb = wxRadioBox(parent=panel, id=rb_id, label=get_m,
                            choices=meths,
                            majorDimension=2, style=wxRA_SPECIFY_COLS)
            rb.SetSelection(self.state_var[i])
            EVT_RADIOBOX(panel, rb_id,
                         lambda event, s=self, i=i: s.radiobox_cb(event, i))
            vert_sizer.Add(rb, flag=wxEXPAND)

        return panel

    def radiobox_cb(self, event, i):
        self.state_var[i] = event.GetEventObject().GetSelection()

    def make_get_set_gui (self, parent):
	"Create the Get/Set methods"

        panel = wxPanel(parent, id=-1)
        grid_sizer = wxGridSizer(cols=2)
        panel.SetAutoLayout(true)
        panel.SetSizer(grid_sizer)
        
	n_meth = len (self.get_set_meths)
	for i in range (0, n_meth):
	    m = "Get"+self.get_set_meths[i]
	    self.get_set_var[i] = eval("self.vtk_obj.%s ()"%m)

	    # if the method requires a color make a button so the user
	    # can choose the color!
	    if string.find (m[-5:], "Color") > -1:
                cbut_id = wxNewId()
                cbut = wxButton(parent=panel, id=cbut_id, label="Set"+m[3:])
                EVT_BUTTON(panel, cbut_id,
                           lambda e, s=self, i=i, p=parent:
                           s.set_color(e, i, p))
                grid_sizer.Add(cbut)
	    else:
                st = wxStaticText(parent=panel, id=-1, label="Set"+m[3:])
                grid_sizer.Add(st)

            self.get_set_texts[i] = wxTextCtrl(parent=panel, id=-1,
                                               value=str(self.get_set_var[i]))
            grid_sizer.Add(self.get_set_texts[i], flag=wxEXPAND)

        return panel

    def make_get_gui (self, master):
	"Create the Get methods that have no Set equivalent."
	frame = Tkinter.Frame (master, relief='ridge', bd=2)
	frame.pack (side='top', expand=1, fill='both')
	n_meth = len (self.get_meths)
	for i in range (0, n_meth):
	    res = eval ("self.vtk_obj.%s ()"% self.get_meths[i])
	    lab = Tkinter.Label (frame, text=self.get_meths[i]+": ")
	    lab.grid (row=i, column=0, sticky='w')
	    self.get_lab[i] = Tkinter.Label (frame, text=res)
	    self.get_lab[i].grid (row=i, column=1, sticky='w')

    def update_gui (self, event=None):
	"Update the values if anything has changed outside."
        if self.vtk_warn > -1:
            self.vtk_obj.GlobalWarningDisplayOff ()

	n_meth = len (self.toggle_meths)
	for i in range (0, n_meth):
	    m = "Get"+self.toggle_meths[i][:-2]
	    self.toggle_var[i].set (eval ("self.vtk_obj.%s ()"%m))

	for i in range (len (self.state_meths)):
	    m = self.state_meths[i]
	    self.state_var[i].set (self.get_state (m))

	n_meth = len (self.get_set_meths)
	for i in range (0, n_meth):
	    m = "Get"+self.get_set_meths[i]
	    self.get_set_var[i].set (eval ("self.vtk_obj.%s ()"%m))
	n_meth = len (self.get_meths)
	for i in range (0, n_meth):
	    res = eval ("self.vtk_obj.%s ()"% self.get_meths[i])
	    self.get_lab[i].config (text=res)

        if self.vtk_warn > -1:
            self.vtk_obj.GlobalWarningDisplayOn ()
	    
    def set_color (self, event, i, parent):
	"Choose and set a color from a GUI color chooser."

        # setup current colour
        cur_colour = wxColour(self.get_set_var[i][0] * 255.0,
                              self.get_set_var[i][1] * 255.0,
                              self.get_set_var[i][2] * 255.0)
        ccd = wxColourData()
        ccd.SetColour(cur_colour)
        # we want the detailed dialog under windows        
        ccd.SetChooseFull(true)
        # do that thang
        dlg = wxColourDialog(parent, ccd)
        
        if dlg.ShowModal() == wxID_OK:
            # the user wants this, we get to update the variables
            new_col = dlg.GetColourData().GetColour()
            self.get_set_var[i] = (float(new_col.Red()) / 255.0 * 1.0,
                                   float(new_col.Green()) / 255.0 * 1.0,
                                   float(new_col.Blue()) / 255.0 * 1.0)
            # now we need to update the frigging text input
            self.get_set_texts[i].SetValue(str(self.get_set_var[i]))

        dlg.Destroy()

    def run_command (self, event=None):
	"Run the command entered by the user."
	st = self.user_command.get ()
	if len (st) == 0:
	    return self.help_user ()
	obj = self.vtk_obj
	try:
	    eval (st)
	except AttributeError, msg:
	    print_err ("AttributeError: %s"%msg)
	except SyntaxError, msg:
	    print_err ("SyntaxError: %s"%msg)
	except NameError, msg:
	    print_err ("NameError: %s"%msg)
	except TypeError, msg:
	    print_err ("TypeError: %s"%msg)
	except ValueError, msg:
	    print_err ("ValueError: %s"%msg)
	except:
	    print_err ("Unhandled exception.  Wrong input.")
	else:
	    self.render ()

    def help_user (self, event=None):
	"Provide help when user clicks the command button."
	msg = "Enter a valid python command.  Please note the "\
	      "following: The name \'obj\' refers to the vtkObject "\
	      "being configured.  Use the function prn(arguments) "\
	      "to print anything.  Use the enter key to run the "\
	      "command.  Example: obj.SetColor(0.1,0.2,0.3)"
	print_info  ("Help", msg)

    def show_doc (self, event=None):
        "Show the class documentation."
        d = VtkShowDoc (self.root)
        d.show_doc (self.vtk_obj)

    def apply_changes (self, event=None):
	"Apply the changes made to configuration."
        if self.vtk_warn > -1:
            self.vtk_obj.GlobalWarningDisplayOff ()

	n_meth = len (self.toggle_meths)
	for i in range (0, n_meth):
	    val = self.toggle_var[i].get ()
	    m = self.toggle_meths[i][:-2]
	    if val == 1:
		eval ("self.vtk_obj.%sOn ()"%m)
	    else:
		eval ("self.vtk_obj.%sOff ()"%m)		

	n_meth = len (self.state_meths)
	for i in range (0, n_meth):
	    val = self.state_var[i].get ()
	    m = self.state_meths[i][val]
	    if val != -1:
		eval ("self.vtk_obj.%s ()"%m)
	
	n_meth = len (self.get_set_meths)
	for i in range (0, n_meth):
	    val = self.get_set_var[i].get ()
	    if string.find (val, "(") == 0:
		val = val[1:-1]
	    st = 0
	    val_tst = eval ("self.vtk_obj.Get%s ()"% self.get_set_meths[i])
	    if type (val_tst) is types.StringType:
		st = 1
	    m = "Set"+self.get_set_meths[i]
	    if st is 0:
		eval ("self.vtk_obj.%s (%s)"%(m, val))
	    else:
		eval ("self.vtk_obj.%s (\"%s\")"%(m, val))

	n_meth = len (self.get_meths)
	for i in range (0, n_meth):
	    res = eval ("self.vtk_obj.%s ()"% self.get_meths[i])
	    self.get_lab[i].config (text=res)

	self.render ()
        if self.vtk_warn > -1:
            self.vtk_obj.SetGlobalWarningDisplay (self.vtk_warn)
		
    def ok_done (self, event=None):
	"Ok button clicked."
	self.apply_changes ()
	self.root.destroy ()

    def cancel (self, event=None):
	"Cancel button clicked."
	self.root.destroy ()

    def render (self):
	"Render scene and update anything that needs updating."
        if self.update_meth and callable (self.update_meth):
            self.update_meth ()
	if self.renwin is not None:
	    try:
		self.renwin.Render ()
	    except:
		pass

    def show (self):
	"Print the various methods of the vtkobject."
	print "Toggle Methods\n", self.toggle_meths
	print "State Methods\n", self.state_meths
	print "Get/Set methods\n", self.get_set_meths
	print "Get methods\n", self.get_meths



if __name__ == "__main__":  
    import vtkpython
    from vtk.wx.wxVTKRenderWindow import wxVTKRenderWindow

    cone = vtkpython.vtkConeSource()
    cone.SetResolution(8)
    coneMapper = vtkpython.vtkPolyDataMapper()
    coneMapper.SetInput(cone.GetOutput())
    coneActor = vtkpython.vtkActor()
    coneActor.SetMapper(coneMapper)
    axes = vtkpython.vtkCubeAxesActor2D ()

    
    app = wxPySimpleApp()
    frame = wxFrame(None, -1, "wxRenderWindow", size=wxSize(400,400))
    wid = wxVTKRenderWindow(frame, -1)
    
    ren = vtkpython.vtkRenderer()
    renWin = wid.GetRenderWindow()
    renWin.AddRenderer(ren)

    ren.AddActor (coneActor)
    ren.AddActor (axes)
    axes.SetCamera (ren.GetActiveCamera ())
    renWin.Render ()

    for obj in (renWin, ren, cone, coneMapper, coneActor,
                coneActor.GetProperty(), axes):
	print "Configuring", obj.GetClassName (), "..."
	conf = ConfigVtkObj (renWin)
	conf.configure (frame, obj)

    app.MainLoop ()
