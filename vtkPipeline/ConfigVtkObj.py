#!/usr/bin/env python
#
# $Id: ConfigVtkObj.py,v 1.1 2002/02/16 00:33:45 cpbotha Exp $
#
# This python program/module takes a VTK object and provides a GUI 
# configuration for it.
#
# Copyright (C) 2000 Prabhu Ramachandran
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

""" This program/module takes a VTK object and provides a GUI
configuration for it.  Right now Tkinter is used for the GUI.

"""

import vtkMethodParser
import types, string, re

try:
    import Tkinter
except ImportError:
    print "Cannot import the Tkinter module. Install it and try again."
    sys.exit (1)

try:
    import tkMessageBox
    import tkColorChooser
except ImportError:
    print "Cannot import the tkMessageBox or tkColorChooser module."
    print "Install the modules and try again."
    sys.exit (1)

print_info = tkMessageBox.showinfo

def print_err (msg):
    tkMessageBox.showerror ("ERROR", msg)

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

    def __init__ (self, master=None):
        self.master = master
        
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
        self.root = Tkinter.Toplevel (self.master)
        self.root.title ("Class Documentation for %s"%
                         self.obj.GetClassName ())
        self.root.protocol ("WM_DELETE_WINDOW", self.quit)
        f = Tkinter.Frame (self.root)
        f.pack (side='top', fill='both', expand=1)
        f.rowconfigure (0, weight=1)
        f.columnconfigure (0, weight=1)
        scr1 = Tkinter.Scrollbar (f, orient='vertical')
        scr2 = Tkinter.Scrollbar (f, orient='horizontal')
        self.txt = Tkinter.Text (f, yscrollcommand=scr1.set,
                                 xscrollcommand=scr2.set,state='normal')
        scr1.config (command=self.txt.yview) 
        scr2.config (command=self.txt.xview) 
        self.txt.grid (row=0, column=0, sticky='ewns')
        scr1.grid (row=0, column=1, sticky='ns')
        scr2.grid (row=1, column=0, columnspan=2, sticky='ew')

        self.close_but = Tkinter.Button (self.root, text="Close", fg="red",
                                         underline=0, command=self.quit)

        self.close_but.pack (side='bottom')
	self.root.bind ("<Alt-c>", self.quit)
            
        self.txt.tag_config ("heading", foreground="blue",
                             underline=1, justify='center')
        self.txt.tag_config ("subheading", foreground="blue",
                             underline=1, justify='left')
        self.txt.tag_config ("item", underline=1, justify='left')
        self.txt.tag_config ("data", wrap='word')
    
    def add_doc (self):
        data_ = self.obj.GetClassName ()
        self.txt.insert ('end', "Class Documentation for %s\n\n"%data_,
                         "heading")
        data_ = self.obj.__doc__ + "\n\n"
        self.txt.insert ('end', data_, "data")
        data_ = "Please note that all the documented methods are not "\
                "configurable using the GUI provided.\n\n\n"
        self.txt.insert ('end', data_, "data")
        
        data_ = "Class method documentation:\n\n"
        self.txt.insert ('end', data_, "subheading")

        for i in dir (self.obj):
            if i == '__class__':
                continue
            try:
                data_ = eval ("self.obj.%s.__doc__"%i)
            except AttributeError:
                pass
            else:
                self.txt.insert ('end', i + ":\n", "item")
                self.txt.insert ('end', data_ +"\n\n", "data")

    def quit (self, event=None):
        self.root.destroy ()


class ConfigVtkObj:

    """ This class finds the methods for a given vtkObject and creates
    a GUI to configure the object.  It uses the output from the
    VtkMethodParser class. """

    def __init__ (self, renwin=None):
	# This vairable is used to do a redraw on changing the objects
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

    def configure (self, master, vtk_obj):
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
	self.make_gui (master)
        if self.vtk_warn > -1:
            self.vtk_obj.SetGlobalWarningDisplay (self.vtk_warn)

    def make_gui (self, master):
	"Makes the configuration GUI."
	self.root = Tkinter.Toplevel (master)
	self.root.title ("Configure %s"%self.vtk_obj.GetClassName ())
        self.root.protocol ("WM_DELETE_WINDOW", self.cancel)
	frame = Tkinter.Frame (self.root)
	frame.pack (side='top', expand=1, fill='both')
	left = Tkinter.Frame (frame)
	left.grid (row=0, column=0, sticky='nw')
	right = Tkinter.Frame (frame)
	right.grid (row=0, column=1, sticky='nw')

	self.make_gui_vars ()
	self.make_control_gui (self.root)
	self.make_toggle_gui (left)
	self.make_state_gui (left)
	self.make_get_gui (right)
	self.make_get_set_gui (right)

    def make_gui_vars (self):
	"Create the various variables used for the GUI."
	self.user_command = Tkinter.StringVar ()
	self.toggle_var = []
	for i in range (0, len (self.toggle_meths)):
	    self.toggle_var.append (Tkinter.IntVar ())
	    self.toggle_var[i].set (-1)

	self.state_var = []
	for i in range (0, len (self.state_meths)):
	    self.state_var.append (Tkinter.IntVar ())
	    self.state_var[i].set (-1)

	self.get_set_var = []
	for i in range (0, len (self.get_set_meths)):
	    self.get_set_var.append (Tkinter.StringVar ())
	    self.get_set_var[i].set ("")

	self.get_lab = []
	for i in range (0, len (self.get_meths)):
	    self.get_lab.append (None)

    def make_control_gui (self, master):
	"Make the main controls and the user command entry."
	frame = Tkinter.Frame (master)
	frame.pack (side='bottom', expand=1, fill='both')
	lab = Tkinter.Label (frame, text="Click on the \"Command\" "\
                             "button for help on it.")
	lab.grid (row=0, column=0, columnspan=4, sticky='ew')
	help = Tkinter.Button (frame, text="Command:", 
                               command=self.help_user)
	help.grid (row=1, column=0, sticky='ew')
	entr = Tkinter.Entry (frame, width=20, relief='sunken', 
                              textvariable=self.user_command)
	entr.grid (row=1, column=1,  columnspan=3, sticky='ew')
	entr.bind ("<Return>", self.run_command)

	help_b = Tkinter.Button (frame, text="Class Documentation",
                                 underline=6, command=self.show_doc)
	help_b.grid (column=0, row=2, padx=2, pady=2, sticky='ew')
	b0 = Tkinter.Button (frame, text="Update", underline=0, 
                             command=self.update_gui)
	b0.grid (column=1, row=2, padx=2, pady=2, sticky='ew')
	b = Tkinter.Button (frame, text="Apply", underline=0,
                            command=self.apply_changes)
	b.grid (column=2, row=2, padx=2, pady=2, sticky='ew')
	b1 = Tkinter.Button (frame, text="Ok", underline=0,
                             command=self.ok_done)
	b1.grid (column=3, row=2, padx=2, pady=2, sticky='ew')
	b2 = Tkinter.Button (frame, text="Cancel", underline=0,
                             command=self.cancel)
	b2.grid (column=4, row=2, padx=2, pady=2, sticky='ew')

	# keyboard accelerators
	self.root.bind ("<Alt-d>", self.show_doc)
	self.root.bind ("<Alt-u>", self.update_gui)
	self.root.bind ("<Alt-a>", self.apply_changes)
	self.root.bind ("<Alt-o>", self.ok_done)
	self.root.bind ("<Alt-c>", self.cancel)

    def make_toggle_gui (self, master):
	"Create the toggle methods.  (On/Off methods)"
	frame = Tkinter.Frame (master, relief='ridge', bd=2)
	frame.pack (side='top', expand=1, fill='both')
	n_meth = len (self.toggle_meths)
	for i in range (0, n_meth):
	    m = "Get"+self.toggle_meths[i][:-2]
	    self.toggle_var[i].set (eval ("self.vtk_obj.%s ()"%m))
	    b = Tkinter.Checkbutton (frame, text=self.toggle_meths[i], 
                                     variable=self.toggle_var[i],
                                     onvalue=1, offvalue=0)
	    b.grid (row=i, column=0, sticky='w')
	    
    def make_state_gui (self, master):
	"Create the state methods.  (SetAToB methods)"
	frame = Tkinter.Frame (master, relief='ridge', bd=2)
	frame.pack (side='top', expand=1, fill='both')
	n_meth = len (self.state_meths)
	rw = 0
	for i in range (0, n_meth):
	    meths = self.state_meths[i]
            self.state_var[i].set (self.get_state (meths))
	    for j in range (0, len (meths)):
		b = Tkinter.Radiobutton (frame, text=meths[j], 
                                         variable=self.state_var[i],
                                         value=j)
		b.grid (row=rw, column=0, sticky='w')
		rw = rw + 1

    def make_get_set_gui (self, master):
	"Create the Get/Set methods"
	frame = Tkinter.Frame (master, relief='ridge', bd=2)
	frame.pack (side='top', expand=1, fill='both')
	n_meth = len (self.get_set_meths)
	for i in range (0, n_meth):
	    m = "Get"+self.get_set_meths[i]
	    self.get_set_var[i].set (eval ("self.vtk_obj.%s ()"%m))

	    # if the method requires a color make a button so the user
	    # can choose the color!
	    if string.find (m[-5:], "Color") > -1:
		but = Tkinter.Button (frame, text="Set"+m[3:],
                                      textvariable=i,
                                      command=lambda e: None, padx=1)
		but.grid (row=i, column=0, sticky='w')
		but.bind ("<1>", self.set_color)
	    else:
		lab = Tkinter.Label (frame, text="Set"+m[3:])
		lab.grid (row=i, column=0, sticky='w')
	    entr = Tkinter.Entry (frame, width=20, relief='sunken', 
                                  textvariable=self.get_set_var[i])
	    entr.grid (row=i, column=1, sticky='ew')

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
	    
    def set_color (self, event=None):
	"Choose and set a color from a GUI color chooser."
	if event is None:
	    return "break"
	# index of the relevant method is stored in the textvariable.
	index = int (event.widget['textvariable'])

	m = "Get"+self.get_set_meths[index]
	col = eval ("self.vtk_obj.%s ()"%m)
	cur_col = "#%02x%02x%02x"% (col[0]*255, col[1]*255, col[2]*255)
	new_color = tkColorChooser.askcolor (title="Set"+m[3:],
					     initialcolor=cur_col)
	if new_color[1] != None:
	    col = tk_2_vtk_color (new_color[0])
	    self.get_set_var[index].set (col)
            m = "Set"+self.get_set_meths[index]
            apply (eval ("self.vtk_obj.%s"%m), col)
            self.update_gui ()

	return "break"

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
    import vtkRenderWidget
    cone = vtkpython.vtkConeSource()
    cone.SetResolution(8)
    coneMapper = vtkpython.vtkPolyDataMapper()
    coneMapper.SetInput(cone.GetOutput())
    coneActor = vtkpython.vtkActor()
    coneActor.SetMapper(coneMapper)
    axes = vtkpython.vtkCubeAxesActor2D ()

    def quit (event=None):
	root.destroy ()

    root = Tkinter.Tk ()
    wid = vtkRenderWidget.vtkTkRenderWidget (root, width=500, height=500)
    wid.pack (expand=1, fill='both')
    wid.bind ("<KeyPress-q>", quit)
    ren = vtkpython.vtkRenderer()
    renWin = wid.GetRenderWindow()
    renWin.AddRenderer(ren)
    renWin.SetSize(500,500)
    ren.AddActor (coneActor)
    ren.AddActor (axes)
    axes.SetCamera (ren.GetActiveCamera ())
    renWin.Render ()

    for obj in (renWin, ren, cone, coneMapper, coneActor, axes):
	print "Configuring", obj.GetClassName (), "..."
	conf = ConfigVtkObj (renWin)
	conf.configure (root, obj)

    root.mainloop ()
