#!/usr/bin/env python
#
# $Id: ConfigVtkObj.py,v 1.25 2005/06/03 09:27:49 cpbotha Exp $
#
# This python program/module takes a VTK object and provides a GUI 
# configuration for it.
#
# This code is distributed under the conditions of the BSD license.
# See LICENSE.txt for details.
#
# Copyright (C) 2000 Prabhu Ramachandran
# Conversion to wxPython, other changes copyright (c) 2002-2005 Charl P. Botha
#
# This software is distributed WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the above copyright notice for more information.
#
# Author contact information:
#   Prabhu Ramachandran <prabhu_r@users.sf.net>
#   http://www.aero.iitm.ernet.in/~prabhu/
#
#   Charl P. Botha <cpbotha@ieee.org>
#   http://cpbotha.net/


"""This program/module takes a VTK object and provides a GUI
configuration for it.

The code, originally by Prabhu Ramachandran, used TkInter as GUI.  That
version is the original one and is actively maintained.  I (Charl Botha)
converted the code to wxPython and made some other changes, primarily
related to making the GUI persistent.
"""

import os # need this for os.path.normpath
import vtkMethodParser
import types, string, re, traceback

try:
    import wx
    import wx.html
    import wx.py
except ImportError:
    print "Cannot import the wxPython.{wx,html} modules. "\
          "Install it and try again."
    sys.exit (1)

try:
    # if we're being run from devide, this should work
    from external.SwitchColourDialog import ColourDialog
except ImportError:
    # if not, fall back to old behaviour (but DO print a warning)
    print "ConfigVtkObj WARNING: could not import external.SwitchColourDialog"
    ColourDialog = wx.ColourDialog

from external.filebrowsebutton import FileBrowseButton, \
     FileBrowseButtonWithHistory,DirBrowseButton

def print_err (msg):
    # create nice formatted string with tracebacks and all
    dmsg = \
         string.join(traceback.format_exception(sys.exc_type,
                                                sys.exc_value,
                                                sys.exc_traceback))
    wx.LogError(dmsg)
    wx.LogError(msg)
    wx.Log_FlushActive()

# use this to print stuff for the user command run from the GUI
def prn (x):
    print x

class VtkShowDoc:
    """ This class displays the documentation included in the __doc__
    attribute of the VTK object and its methods.

    Instantiate the class with a parent_frame and the vtk object which
    it should examine.  Then call show().  The display can be hidden with
    hide().  The window can be destroyed with close().  A normal window
    close will only hide() the window."""

    def __init__ (self, parent_frame, vtk_obj):
        self._parent_frame = parent_frame
        self._vtk_obj = vtk_obj

        if self._check_obj():
            self._create_ui()
            self._add_doc()
        
    def _check_obj (self):
        try:
            self._vtk_obj.GetClassName ()
        except AttributeError:            
            msg = "Sorry! The object passed does not seem to be a "\
                  "VTK object!!"
            print_err (msg)
            return 0
        try:
            doc_ = self._vtk_obj.__doc__
        except AttributeError:
            msg = "Sorry! This particular version of the VTK-Python "\
                  "bindings does not feature embedded documentation "\
                  "of the class and its methods.  Please use a more "\
                  "up to date version of VTK."
            print_err (msg)
            return 0
        else:
            return 1

    def _create_ui(self):
        self._frame = wx.Frame(parent = self._parent_frame, id=-1,
                              title='Class Documentation for %s' %
                              self._vtk_obj.GetClassName ())
        wx.EVT_CLOSE(self._frame, lambda e, s=self: s.hide())

        # make panel that will contain htmlwindow and close button
        panel = wx.Panel(parent=self._frame, id=-1)

        # then the html window
        self._html_window = wx.html.HtmlWindow(parent=panel, id=-1,
                                               size=wx.Size(640,480))

        close_id = wx.NewId()
        close_button = wx.Button(parent=panel, id=close_id, label="Close")
        wx.EVT_BUTTON(self._frame, close_id, lambda e, s=self: s.hide())

        top_sizer = wx.BoxSizer(wx.VERTICAL)
        top_sizer.Add(self._html_window, option=1, flag=wx.EXPAND)
        top_sizer.Add(close_button, option=0, flag=wx.ALIGN_CENTER_HORIZONTAL)

        panel.SetAutoLayout(True)
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

    
    def _add_doc (self):
        data_ = self._vtk_obj.GetClassName ()

        the_html = "<h1>Class Documentation for %s</h1><br><br>" % data_

        the_html = the_html + \
                   string.join(string.split(self._vtk_obj.__doc__, '\n'),
                               '<br>')
        the_html = the_html + '<br><br>' + \
                   "Please note that all the documented methods are not "\
                   "configurable using the GUI provided.<br><br><br>"\
                   "<h2>Class method documentation</h2><br><br>"

        for i in dir (self._vtk_obj):
            if i == '__class__':
                continue
            try:
                data_ = eval ("self._vtk_obj.%s.__doc__"%i)
            except AttributeError:
                pass
            else:
                the_html = the_html + \
                           "<h3>" + i + ":</h3><br>" + \
                           string.join(string.split(data_,'\n'),'<br>') + \
                           "<br><br>"

        self._html_window.SetPage(the_html)

    def show(self):
        "Make the show doc frame visible."
        self._frame.Show(True)
        self._frame.Raise()

    def hide(self):
        "Make the show doc frame invisible."
        self._frame.Show(False)

    def close(self, event=None):
        """Destroy the frame completely.

        You can check if the frame has been destroyed by checking for
        ._frame == None.
        """
        self._frame.Destroy()
        self._frame = None


class ConfigVtkObj:
    """ This class finds the methods for a given vtkObject and creates
    a GUI to configure the object.

    It uses the output from the VtkMethodParser class.  In order to use it,
    construct an instance, then call show().  If the user closes the window,
    it will only be hidden, not destroyed.  To destroy, you have to call
    close().

    These show()/hide() semantics have been added to make it easier to have
    persistent ConfigVtkObj's.  Please see the end of vtkPipeline for an
    example.

    If frame and panel are NOT None, ConfigVtkObj will generate its UI
    into the given frame and panel.  The panel that you pass HAS to have
    a top-level sizer.
    """
    def __init__ (self, parent, renwin, vtk_obj,
                  frame=None, panel=None):
        """This initialiser will setup everything and construct the ui.

        You have to call show() to make it appear, however.
        """
	# This variable is used to do a redraw on changing the objects
	# properties.
        self._parent = parent
	self._renwin = renwin
        self._vtk_obj = vtk_obj

        if frame and panel:
            self._frame = frame
            self._panel = panel
            self._ownFrameAndPanel = False
        else:
            self._frame = None
            self._panel = None
            self._ownFrameAndPanel = True
        
	self.parser = vtkMethodParser.VtkMethodParser ()
	self.state_patn = re.compile ("To[A-Z0-9]")
        self.update_meth = None
        # create that ui
        self.create_ui()

    def create_ui(self):
        "Internal function called by constructor to create user interface."
        self.vtk_warn = -1
        try:
            self.vtk_warn = self._vtk_obj.GetGlobalWarningDisplay ()
        except AttributeError:
            pass
        else:
            self._vtk_obj.GlobalWarningDisplayOff ()

        # make lists of all the methods available in the vtk_object
	self.parse_methods (self._vtk_obj)

        # ################################################################
        # now create all the actual widget/ui elements
        # ################################################################
        if self._ownFrameAndPanel:
            self._frame = wx.Frame(parent=self._parent, id=-1,
                                  title="Configure %s"%
                                  self._vtk_obj.GetClassName ())
            # if the user closes the frame, we just hide ourselves (tee hee)
            wx.EVT_CLOSE(self._frame, lambda e, s=self: s.hide())

            # then the panel which we'll populate
            self._panel = wx.Panel(parent=self._frame, id=-1)

        # first with a vertical sizer, settings at the top, buttons
        # + controls at the bottom - this sizer7 will have a 7px border
        sizer7 = wx.BoxSizer(wx.VERTICAL)

        self._notebook = wx.Notebook(parent=self._panel, id=-1,
                                    size=(640,480))
        nbsizer = wx.NotebookSizer(self._notebook)

        sizer7.Add(nbsizer, option=0,
                   flag=wx.EXPAND)

	self.make_gui_vars ()

        # the sizer returned by make_control_gui has no border... we want
        # a border of 7 between the control_gui and the notebook
	sizer7.Add(self.make_control_gui(self._panel), option=1,
                   flag=wx.EXPAND|wx.TOP, border=7)
        
	self._notebook.AddPage(self.make_toggle_gui(self._notebook), 'Toggles')
        self._notebook.AddPage(self.make_state_gui(self._notebook), 'States')
        self._notebook.AddPage(self.make_get_gui(self._notebook), 'Gets')
        self._notebook.AddPage(self.make_get_set_gui(self._notebook),
                               'Get-Set')


        if self._ownFrameAndPanel:
            topSizer = wx.BoxSizer(wx.VERTICAL)
            topSizer.Add(sizer7, 1, wx.ALL|wx.EXPAND, 7)
        
            self._panel.SetAutoLayout(True)
            self._panel.SetSizer(topSizer)
            topSizer.Fit(self._frame)
            topSizer.SetSizeHints(self._frame)
        else:
            # we assume the given panel already has a sizer
            self._panel.GetSizer().Add(sizer7, 1, wx.ALL|wx.EXPAND, 7)

        if self.vtk_warn > -1:
            self._vtk_obj.SetGlobalWarningDisplay (self.vtk_warn)

        # now some variables we'll need for transient parts of the gui
        self._vtk_obj_doc_view = None

    def configure(self, parent_frame, vtk_obj):
        print "ConfigVtkObj() is now deprecated!"

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
        orig = eval ("self._vtk_obj.%s()"%get_m)
        for i in range (len(meths)):
            m = meths[i]
            eval ("self._vtk_obj.%s()"%m)
            val = eval ("self._vtk_obj.%s()"%get_m)
            if val == orig:
                break
        return i

    def show(self):
        self._frame.Show(True)
        self._frame.Raise()

    def hide(self):
        self._frame.Show(False)

    def make_gui_vars (self):
	"Create the various variables used for the GUI."
	#self.user_command = Tkinter.StringVar ()

	self.toggle_var = [-1 for i in self.toggle_meths]
        self.toggle_checkboxes = [None for i in self.toggle_var]
        
        self.state_var = [-1 for i in self.state_meths]
        self.state_radioboxes = [None for i in self.state_var]
        
        self.get_set_var = ["" for i in self.get_set_meths]
        self.get_set_texts = [None for i in self.get_set_var]
        
        self.get_texts = [None for i in self.get_meths]

    def make_control_gui (self, parent):
        """Makes all the control GUI elements.

        This will create the control buttons and the command line
        interface bit.  All the controls must be children of the parameter
        parent.  This method must return a sizer that can be added to the
        top level sizer.
        """
        vert_sizer = wx.BoxSizer(wx.VERTICAL)
        command_sizer = wx.BoxSizer(wx.HORIZONTAL)

        vert_sizer.Add(command_sizer, option=1, flag=wx.EXPAND)

        command_entry = wx.py.shell.Shell(parent=parent, id=-1,
                                          introText="'obj' is bound to the " \
                                          "introspected object.",
                                          size=(400,200), style=0,
                                          locals={'obj' : self._vtk_obj})
        command_sizer.Add(command_entry, option=1, flag=wx.EXPAND)


        if self._ownFrameAndPanel:
            # we only make the command buttons if we're NOT being put
            # into someone else's panel
            button_sizer = wx.BoxSizer(wx.HORIZONTAL)
            vert_sizer.Add(button_sizer, 0, wx.TOP|wx.ALIGN_RIGHT,
                           7)
            
            apply_id = wx.NewId()
            apply_button = wx.Button(parent, id=apply_id,
                                     label="Apply")
            button_sizer.Add(apply_button, 0, wx.RIGHT, 7)
            wx.EVT_BUTTON(parent, apply_id, lambda e, s=self: s.apply_changes())
            apply_button.SetToolTip(wx.ToolTip(
                'Modify configuration of the underlying class as specified ' \
                'by this dialogue.'))

            # we can't make this default... everytime somebody presses
            # the enter button in the command window, BOOM
            #apply_button.SetDefault()

            closeButtonId = wx.NewId()
            closeButton = wx.Button(parent, closeButtonId, label="Close")
            button_sizer.Add(closeButton, 0, wx.RIGHT, 7)
            wx.EVT_BUTTON(parent, closeButtonId, lambda e, s=self: s.cancel())
            closeButton.SetToolTip(wx.ToolTip(
                'Hide this dialogue without applying changes.'))


            syncButtonId = wx.NewId()
            syncButton = wx.Button(parent, syncButtonId,
                                  label="Sync")
            button_sizer.Add(syncButton, 0, wx.RIGHT, 7)
            wx.EVT_BUTTON(parent, syncButtonId, lambda e, s=self: s.update_gui())
            syncButton.SetToolTip(wx.ToolTip(
                'Synchronise this dialogue with the configuration of the ' \
                'underlying class.'))

            classdoc_id = wx.NewId()
            classdoc_button = wx.Button(parent, id=classdoc_id,
                                       label="Class Documentation")
            button_sizer.Add(classdoc_button, 0, wx.RIGHT, 7)
            wx.EVT_BUTTON(parent, classdoc_id, lambda e, s=self: s.show_doc())
            classdoc_button.SetToolTip(wx.ToolTip(
                'Show class documentation for the current class.'))

        return vert_sizer

    def make_toggle_gui (self, parent):
	"""Create the toggle methods.

        This method should do whatever it does into a panel that it creates.
        This panel should be returned, as it's going to be stuffed in a
        notebook, typically the parent.  Remember that the panel should be
        child to the parent.
        """
        panel = wx.Panel(parent, id=-1)
        vert_sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetAutoLayout(True)
        panel.SetSizer(vert_sizer)

        internalSizer = wx.BoxSizer(wx.VERTICAL)
        vert_sizer.Add(internalSizer, 1, wx.ALL, 7)
        
	n_meth = len (self.toggle_meths)
	for i in range (0, n_meth):
	    m = "Get"+self.toggle_meths[i][:-2]
	    self.toggle_var[i] = eval ("self._vtk_obj.%s ()"%m)
            cb_id = wx.NewId()
            cb = wx.CheckBox(parent=panel, id=cb_id, label=self.toggle_meths[i])
            cb.SetValue(self.toggle_var[i])
            wx.EVT_CHECKBOX(panel, cb_id,
                         lambda event, s=self, i=i: s.toggle_cb(event, i))

            # find docstring for GetMethod() and add it as tooltip
            try:
                docString = eval('self._vtk_obj.%s.__doc__' % (m,))
            except AttributeError:
                pass
            else:
                cb.SetToolTip(wx.ToolTip(docString))
                
            internalSizer.Add(cb, option=0, flag=wx.EXPAND)
            self.toggle_checkboxes[i] = cb

        return panel

    def toggle_cb(self, event, i):
        """Event handler to simulate tk's groovy active variables.

        When the user clicks a checkbox, this callback gets triggered and
        modifies our internal variable.  Neat.
        """
        self.toggle_var[i] = event.GetEventObject().GetValue()
	    
    def make_state_gui (self, parent):
	"Create the state methods.  (SetAToB methods)"
        panel = wx.Panel(parent, id=-1)
        vert_sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetAutoLayout(True)
        panel.SetSizer(vert_sizer)

        internalSizer = wx.BoxSizer(wx.VERTICAL)
        vert_sizer.Add(internalSizer, 1, wx.ALL, 7)

        # self.state_meths is a list of lists
        # each of the contained lists is the collection of SetBlaToBlaat
        # methods, where Bla is constant for each contained list
	n_meth = len (self.state_meths)
	rw = 0

	for i in range (0, n_meth):
	    meths = self.state_meths[i]
            # a subgroup must have more than 1 member, else it's not a state method
            if len(meths) > 1:
                self.state_var[i] = self.get_state (meths)

                # these 2 lines ripped from get_state
                end = self.state_patn.search (meths[0]).start ()
                get_m = 'G'+meths[0][1:end]
            
                rb_id = wx.NewId()
                rb = wx.RadioBox(parent=panel, id=rb_id, label=get_m,
                                choices=meths,
                                majorDimension=2, style=wx.RA_SPECIFY_COLS)
                rb.SetSelection(self.state_var[i])

                set_m = meths[0][0:end]
                try:
                    docString = eval('self._vtk_obj.%s.__doc__' % (set_m,))
                except AttributeError:
                    pass
                else:
                    rb.SetToolTip(wx.ToolTip(docString))
                    

                wx.EVT_RADIOBOX(panel, rb_id,
                             lambda event, s=self, i=i: s.radiobox_cb(event, i))
                internalSizer.Add(rb, 0, wx.EXPAND|wx.BOTTOM, 7)
                self.state_radioboxes[i] = rb

        return panel

    def radiobox_cb(self, event, i):
        self.state_var[i] = event.GetEventObject().GetSelection()

    def make_get_set_gui (self, parent):
	"Create the Get/Set methods"

        panel = wx.Panel(parent, id=-1)

        vertSizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetAutoLayout(True)
        panel.SetSizer(vertSizer)
        
        grid_sizer = wx.FlexGridSizer(cols=2, vgap=7, hgap=3)
        grid_sizer.AddGrowableCol(1)
        vertSizer.Add(grid_sizer, 1, wx.EXPAND|wx.ALL, 7)
        
	n_meth = len (self.get_set_meths)
	for i in range (0, n_meth):
	    m = "Get"+self.get_set_meths[i]
	    self.get_set_var[i] = eval("self._vtk_obj.%s ()"%m)

            s = 'Set'+self.get_set_meths[i]
            try:
                docString = eval('self._vtk_obj.%s.__doc__' % (s,))
            except AttributeError:
                docString = None

	    # if the method requires a colour make a button so the user
	    # can choose the colour!
	    if string.find (m[-5:], "Color") > -1:
                cbut_id = wx.NewId()
                cbut = wx.Button(parent=panel, id=cbut_id, label="Set"+m[3:])
                wx.EVT_BUTTON(panel, cbut_id,
                           lambda e, s=self, i=i, p=parent:
                           s.set_color(e, i, p))
                grid_sizer.Add(cbut, 0, wx.ALIGN_CENTER_VERTICAL)

                if docString:
                    cbut.SetToolTip(wx.ToolTip(docString))

	    else:
                st = wx.StaticText(parent=panel, id=-1, label="Set"+m[3:])
                grid_sizer.Add(st, 0, wx.ALIGN_CENTER_VERTICAL)

                if docString:
                    st.SetToolTip(wx.ToolTip(docString))

            if m.endswith('FileName'):
                if docString:
                    toolTip = docString
                else:
                    toolTip = "Type filename or click browse to choose file"

                fbb = FileBrowseButton(
                    panel, -1,
                    toolTip=toolTip,
                    labelText=None,
                    changeCallback=lambda evt, i=i:
                    self.handlerGetSetFileBrowseButton(evt, i))

                # set initial value of the text entry
                fbb.SetValue(str(self.get_set_var[i]))

                # store a binding to the widget in the normal place
                self.get_set_texts[i] = fbb
                
                # add the thing to the sizer
                grid_sizer.Add(self.get_set_texts[i], 0,
                               wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
                
                
            else:
                gst_id = wx.NewId()
                self.get_set_texts[i] = wx.TextCtrl(
                    parent=panel, id=gst_id,
                    value=str(self.get_set_var[i]))

                if docString:
                    self.get_set_texts[i].SetToolTip(wx.ToolTip(docString))
                
                wx.EVT_TEXT(parent, gst_id,
                         lambda event, s=self, i=i: s.get_set_cb(event, i))
                grid_sizer.Add(self.get_set_texts[i],
                               flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)

        return panel

    def get_set_cb(self, event, i):
        # let's be naughty...
        self.get_set_var[i] = event.GetEventObject().GetValue()

    def handlerGetSetFileBrowseButton(self, evt, i):
        self.get_set_var[i] = evt.GetString()

    def make_get_gui (self, parent):
	"Create the Get methods that have no Set equivalent."
        panel = wx.Panel(parent, id=-1)

        vertSizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetAutoLayout(True)
        panel.SetSizer(vertSizer)
        
        grid_sizer = wx.FlexGridSizer(cols=2)
        grid_sizer.AddGrowableCol(1)
        vertSizer.Add(grid_sizer, 1, wx.ALL, 7)
        
	n_meth = len (self.get_meths)
	for i in range (0, n_meth):
	    res = eval ("self._vtk_obj.%s ()"% self.get_meths[i])
            st = wx.StaticText(parent=panel, id=-1, label=self.get_meths[i]+":")
            grid_sizer.Add(st)

            st2 = wx.StaticText(parent=panel, id=-1, label=str(res))
            grid_sizer.Add(st2, flag=wx.EXPAND)

            self.get_texts[i] = st2

            try:
                docString = eval('self._vtk_obj.%s.__doc__' %
                                 (self.get_meths[i],))
            except AttributeError:
                pass
            else:
                st.SetToolTip(wx.ToolTip(docString))
                st2.SetToolTip(wx.ToolTip(docString))
            

        return panel

    def update_gui (self, event=None):
	"Update the values if anything has changed outside."
        if self.vtk_warn > -1:
            self._vtk_obj.GlobalWarningDisplayOff ()

	n_meth = len (self.toggle_meths)
	for i in range (0, n_meth):
	    m = "Get"+self.toggle_meths[i][:-2]
	    self.toggle_var[i] = eval ("self._vtk_obj.%s ()"%m)
            # set value does NOT invoke the callback
            self.toggle_checkboxes[i].SetValue(self.toggle_var[i])

	for i in range (len (self.state_meths)):
	    m = self.state_meths[i]
	    self.state_var[i] = self.get_state (m)
            self.state_radioboxes[i].SetSelection(self.state_var[i])

	n_meth = len (self.get_set_meths)
	for i in range (0, n_meth):
	    m = "Get"+self.get_set_meths[i]
	    self.get_set_var[i] = eval("self._vtk_obj.%s ()"%m)
            self.get_set_texts[i].SetValue(str(self.get_set_var[i]))
            
	n_meth = len (self.get_meths)
	for i in range (0, n_meth):
	    res = eval ("self._vtk_obj.%s ()"% self.get_meths[i])
	    self.get_texts[i].SetLabel(str(res))

        if self.vtk_warn > -1:
            self._vtk_obj.GlobalWarningDisplayOn ()
	    
    def set_color (self, event, i, parent):
	"Choose and set a color from a GUI color chooser."

        # setup current colour
        # we need to convert get_set_var[i], which could be string, to
        # a tuple...
        exec('colour_tuple = %s' % str(self.get_set_var[i]))
        cur_colour = wx.Colour(colour_tuple[0] * 255.0,
                              colour_tuple[1] * 255.0,
                              colour_tuple[2] * 255.0)
        ccd = wx.ColourData()
        ccd.SetColour(cur_colour)
        # often-used BONE custom colour
        ccd.SetCustomColour(0,wx.Colour(255, 239, 219))
        # we want the detailed dialog under windows        
        ccd.SetChooseFull(True)
        # do that thang
        dlg = ColourDialog(parent, ccd)
        
        if dlg.ShowModal() == wx.ID_OK:
            # the user wants this, we get to update the variables
            new_col = dlg.GetColourData().GetColour()
            self.get_set_var[i] = (float(new_col.Red()) / 255.0 * 1.0,
                                   float(new_col.Green()) / 255.0 * 1.0,
                                   float(new_col.Blue()) / 255.0 * 1.0)
            # now we need to update the frigging text input (and this is going
            # to trigger the callback in anycase, which is going to repeat the
            # line above, but with text)
            self.get_set_texts[i].SetValue(str(self.get_set_var[i]))

        dlg.Destroy()

    def show_doc (self, event=None):
        "Show the class documentation."
        if self._vtk_obj_doc_view == None:
            self._vtk_obj_doc_view = VtkShowDoc(self._frame, self._vtk_obj)
        self._vtk_obj_doc_view.show()

    def apply_changes (self, event=None):
	"Apply the changes made to configuration."
        if self.vtk_warn > -1:
            self._vtk_obj.GlobalWarningDisplayOff ()

	n_meth = len (self.toggle_meths)
	for i in range (0, n_meth):
	    val = self.toggle_var[i]
	    m = self.toggle_meths[i][:-2]
	    if val == 1:
		eval ("self._vtk_obj.%sOn ()"%m)
	    else:
		eval ("self._vtk_obj.%sOff ()"%m)		

	n_meth = len (self.state_meths)
	for i in range (0, n_meth):
	    val = self.state_var[i]
	    m = self.state_meths[i][val]
	    if val != -1:
		eval ("self._vtk_obj.%s ()"%m)
	
	n_meth = len (self.get_set_meths)
	for i in range (0, n_meth):
	    val = str(self.get_set_var[i])
	    if string.find (val, "(") == 0:
		val = val[1:-1]

	    val_tst = eval ("self._vtk_obj.Get%s ()"% self.get_set_meths[i])

            if type (val_tst) is types.StringType: 
		st = 1
            elif self.get_set_meths[i].endswith('FileName'):
                # we make an exception with Get/SetFilename
                if val == 'None' or val == '':
                    val = None
                    st = 0
                else:
                    st = 1

            else:
                st = 0
                
                
	    m = "Set"+self.get_set_meths[i]
	    if st is 0:
		eval ("self._vtk_obj.%s (%s)"%(m, val))
	    else:
                # we have to use raw strings here, so things like \r
                # don't throw it... mmmkay?
		eval ("self._vtk_obj.%s (r\"%s\")"%(m, val))

	n_meth = len (self.get_meths)
	for i in range (0, n_meth):
	    res = eval ("self._vtk_obj.%s ()"% self.get_meths[i])
	    self.get_texts[i].SetLabel(str(res))

	self.render ()
        if self.vtk_warn > -1:
            self._vtk_obj.SetGlobalWarningDisplay (self.vtk_warn)
		
    def cancel (self, event=None):
	"Cancel button clicked."
        self.hide()

    def close(self):
        """This method will delete all bindings to VTK objects and kill the
        UI.

        Make sure to call this method if you want to make sure that examined
        VTK objects will gracefully self-destruct eventually.  If you don't
        call this, it could take a very long while before the Python garbage
        collector gets to us.
        """
        
        # make sure we get rid of our reference to the _vtk_obj, else
        # it may never disappear
        del self._vtk_obj
        # also lose our renwin binding, thank you
        del self._renwin
        if self._ownFrameAndPanel:
            # now get rid of the user interface as well
            self._frame.Destroy()
        else:
            # these are not ours, just remove our bindings
            del self._frame
            del self._panel
        

    def render(self):
	"Render scene and update anything that needs updating."
        if self.update_meth and callable (self.update_meth):
            self.update_meth ()
	if self._renwin is not None:
	    try:
		self._renwin.Render ()
	    except:
		pass

    def show_vtkobject_methods(self):
	"Print the various methods of the vtkobject."
	print "Toggle Methods\n", self.toggle_meths
	print "State Methods\n", self.state_meths
	print "Get/Set methods\n", self.get_set_meths
	print "Get methods\n", self.get_meths


if __name__ == "__main__":  
    import vtkpython
    from vtk.wx.VTKRenderWindow import VTKRenderWindow

    cone = vtkpython.vtkConeSource()
    cone.SetResolution(8)
    coneMapper = vtkpython.vtkPolyDataMapper()
    coneMapper.SetInput(cone.GetOutput())
    coneActor = vtkpython.vtkActor()
    coneActor.SetMapper(coneMapper)
    axes = vtkpython.vtkCubeAxesActor2D ()

    
    app = wx.PySimpleApp()
    frame = wx.Frame(None, -1, "wx.RenderWindow", size=wx.Size(400,400))
    wid = wx.VTKRenderWindow(frame, -1)
    
    ren = vtkpython.vtkRenderer()
    renWin = wid.GetRenderWindow()
    renWin.AddRenderer(ren)

    ren.AddActor (coneActor)
    ren.AddActor (axes)
    axes.SetCamera (ren.GetActiveCamera ())
    renWin.Render ()

#    for obj in (renWin, ren, cone, coneMapper, coneActor,
#                coneActor.GetProperty(), axes):
#	print "Configuring", obj.GetClassName (), "..."
#	conf = ConfigVtkObj(frame, renWin, obj)
#        conf.show()

    r = vtkpython.vtkXMLPolyDataReader()
    conf = ConfigVtkObj(frame, None, r)
    conf.show()

    app.MainLoop ()
