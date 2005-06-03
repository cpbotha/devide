#!/usr/bin/env python
#
# $Id: vtkPipeline.py,v 1.8 2005/06/03 09:27:49 cpbotha Exp $
#
# This python program/module creates a graphical VTK pipeline browser.  
# The objects in the pipeline can be configured.
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


""" This python program/module creates a graphical VTK pipeline
browser.

The objects in the pipeline can be configured.  The configuration is
done by using the ConfigVtkObj class.
"""

import wx
import os, string, re, types
import ConfigVtkObj

# set this to 1 if you want to see debugging messages - very useful if
# you have problems
DEBUG=0
def debug (msg):
    if DEBUG:
	print msg

# A hack to prevent vtkTransform.GetInverse() infinite loops
last_transform = 0

icon_map = {'RenderWindow': 'renwin', 'Renderer': 'ren',
            'Actor': 'actor', 'Light': 'light', 'Camera': 'camera',
            'Mapper': 'process', 'Property': 'file',
	    'Coordinate': 'coord', 'Source': 'data', 
            'LookupTable': 'colormap', 'Reader': 'data',
            'Assembly': 'actor', 'Python': 'python', 'Dummy1': 'question'}

def get_icon (vtk_obj):
    if not hasattr(vtk_obj, 'GetClassName'):
        return None
    
    strng = vtk_obj.GetClassName ()[3:]
    for key in icon_map.keys ():
	if string.find (strng, key) > -1:
	    return [key, vtk_obj, icon_map[key]]
    return ["", vtk_obj, "question"]


def remove_method (name, methods, method_names):
    "Removes methods if they have a particular name."
    
    debug ("vtkPipeline.py: remove_methods(\'%s\', methods, "\
           "method_names)"%name)
    try:
        idx = method_names.index(name)
    except ValueError:
        pass
    else:
        del methods[idx], method_names[idx]
    return methods, method_names
    

def get_methods (vtk_obj):
    """Obtain the various methods from the passed object.  This
    function also cleans up the method names to check for."""

    debug ("vtkPipeline.py: get_methods(vtk_obj)")
    methods = str (vtk_obj)
    methods = string.split (methods, "\n")
    del methods[0]

    # using only the first set of indented values.
    patn = re.compile ("  \S")
    for method in methods[:]:
	if patn.match (method):
            if string.find (method, ":") == -1:
                methods.remove (method)
            elif string.find (method[1], "none") > -1:
                methods.remove (method)	
        else:
	    methods.remove (method)    

    method_names = []
    for i in range (0, len (methods)):
	strng = methods[i]
	strng = string.replace (strng, " ", "")
	methods[i] = string.split (strng, ":")
        method_names.append (methods[i][0])
        
    # Bug! :(
    # Severe bug - causes segfault with readers and renderwindows on
    # older VTK releases    
    if re.match ("vtk\w*RenderWindow", vtk_obj.GetClassName ()) or \
       re.match ("vtk\w*Reader", vtk_obj.GetClassName ()):
        remove_method('FileName', methods, method_names)
        
    if re.match ("vtk\w*Renderer", vtk_obj.GetClassName ()):
	methods.append (["ActiveCamera", ""])

    if re.match ("vtk\w*Assembly", vtk_obj.GetClassName ()):
        methods.append (["Parts", ""])
        methods.append (["Volumes", ""])
        methods.append (["Actors", ""])

    # fixes bug with infinite loop for GetInverse() method.  Thanks to
    # "Blezek, Daniel J" <blezek@crd.ge.com> for reporting it.    
    global last_transform
    if vtk_obj.IsA('vtkAbstractTransform'):
        if last_transform:
            remove_method('Inverse', methods, method_names)
        else:
            last_transform = last_transform + 1
    else:
        last_transform = 0

    # Some of these object are removed because they arent useful in
    # the browser.  I check for Source and Input anyway so I dont need
    # them.    
    for name in ('Output', 'FieldData', 'CellData', 'PointData',
                 'Source', 'Input'):
        remove_method(name, methods, method_names)
    
    return methods


# A new idea - more general.  Using this I can obtain a lot more
# objects in the pipeline
def get_vtk_objs (vtk_obj):
    "Obtain vtk objects from the passed objects."

    debug ("vtkPipeline.py: get_vtk_objs (%s)"%
	   (vtk_obj.GetClassName ()))
           
    methods = get_methods(vtk_obj)

    vtk_objs = []
    for method in methods:
	try:
	    t = eval ("vtk_obj.Get%s ().GetClassName ()"%method[0])
	except:
	    pass
	else:
	    if string.find (t, "Collection") > -1:		
		col = eval ("vtk_obj.Get%s ()"%method[0])
		col.InitTraversal ()
		n = col.GetNumberOfItems ()
		prop = 0
		if re.match ("vtkProp\w*C", t):
		    prop = 1
		for i in range (0, n):
		    if prop:
			obj = col.GetNextProp ()
		    else:
			obj = col.GetNextItem ()
		    icon = get_icon (obj)
                    if icon:
                        vtk_objs.append (["%s%d"%(icon[0], i), obj, icon[2]])
	    else:
		obj = eval ("vtk_obj.Get%s ()"%method[0])
                icon = get_icon(obj)
                if icon:
                    vtk_objs.append (icon)

    icon = icon_map['Source']
    try:
        obj = vtk_obj.GetSource ()
    except:
        pass
    else:
        if obj:
            vtk_objs.append (["Source", obj, icon])
    try: 
        n_s = vtk_obj.GetNumberOfSources ()
    except:
        pass
    else:
        for i in range (0, n_s):
            obj = vtk_obj.GetSource (i)
            vtk_objs.append (["Source%d"%i, obj, icon])

    try:  
        obj = vtk_obj.GetInput ()
    except:  
        pass
    else:
        if obj:
            icon = get_icon (obj)
            if icon:
                vtk_objs.append (icon)
    
    return vtk_objs

def recursively_add_children(tree_ctrl, parent_node):
    """Utility function to fill out wx.TreeCtrl.

    Pass this function a wx.TreeCtrl and _a_ node, and it will fill out
    everything below it by using Prabhu's code.
    """
    
    children = get_vtk_objs(tree_ctrl.GetPyData(parent_node))
    for i in children:
        # vtkExecutive causes infinite recursion: each vtkAlgorithm (all
        # ProcessObjects, amongst others) is managed by a vtkExecutive,
        # so we get the Executive as a child object (via GetExecutive()),
        # and then the ProcessObject as its child (via GetAlgorithm()), and
        # then ping pong into flaming death.
        if not i[1].IsA("vtkRenderWindowInteractor") and \
               not i[1].IsA("vtkExecutive"):

            # get_vtk_objs() conveniently calls get_icon as well
            img_idx = icon_map.values().index(i[2])
            if i[0]:
                text = i[0] + " (" + i[1].GetClassName() + ")"
            else:
                text = i[1].GetClassName()
                
            # now add the node with image index
            ai = tree_ctrl.AppendItem(parent_node, text, img_idx)
            # and set the data to be the actual vtk object
            tree_ctrl.SetPyData(ai, i[1])
        
            # and we get to call ourselves!
            recursively_add_children(tree_ctrl, ai)

class vtkPipelineBrowser:
    """Browses the VTK pipleline given a vtkRenderWindow or given a set of
    VTK objects, in which case it shows pipeline segments.

    Construct a vtkPipeline with the correct parameters (see the __init__()
    documentation, then use show() to display the window.  Closing the window
    will NOT destroy it, it will only cause a hide().  To destroy the window,
    make use of the vtkPipelineBrowser.close() method from the calling code.
    """

    def __init__ (self, parent, renwin, objs=None):
        """Constructor of the vtkPipelineBrowser.

        If objs == None, this class assumes that you want a full pipeline
        which it will extract starting at the renwin.  If you have some
        vtk objects however, this class will act as a segment browser with
        those objects as the root nodes.  In the latter case, the renwin
        will still be used for performing updates.
        """
        
	self.renwin = renwin
        self._objs = objs

        # this will be a dictionary of already existing ConfigVtkObj's using
        # the vtk_obj as key... this is to enable us to lookup already running
        # instances and just reactivate them
        self._config_vtk_objs = {}

        self._frame = wx.Frame(parent=parent, id=-1,
                              title="VTK Pipeline Browser")
        wx.EVT_CLOSE(self._frame, lambda e: self.hide())

        panel = wx.Panel(parent=self._frame, id=-1)

        tree_id = wx.NewId()
        self._tree_ctrl = wx.TreeCtrl(parent=panel,
                                     id=tree_id,
                                     size=wx.Size(300,400),
                                     style=wx.TR_HAS_BUTTONS)
        
        wx.EVT_TREE_ITEM_ACTIVATED(panel, tree_id, self.item_activate_cb)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        refr_id = wx.NewId()
        refr = wx.Button(parent=panel, id=refr_id, label="Refresh")
        wx.EVT_BUTTON(panel, refr_id, self.refresh)
        button_sizer.Add(refr)

        q_id = wx.NewId()
        q = wx.Button(parent=panel, id=q_id, label="Close")
        wx.EVT_BUTTON(panel, q_id, lambda e, s=self: s.hide())
        button_sizer.Add(q)

        top_sizer = wx.BoxSizer(wx.VERTICAL)

        top_sizer.Add(self._tree_ctrl, option=1, flag=wx.EXPAND)
        top_sizer.Add(button_sizer, option=0, flag=wx.ALIGN_CENTER_HORIZONTAL)

        panel.SetAutoLayout(True)
        panel.SetSizer(top_sizer)
        top_sizer.Fit(self._frame)
        top_sizer.SetSizeHints(self._frame)

        #self._frame.Show(True)

        ICONDIR = "Icons"

        # Look for Icons subdirectory in the same directory as this module
        try:
            # handling frozen installs.
            home, exe = os.path.split(sys.executable)
            if string.lower(exe[:6]) == 'python':
                _icondir = os.path.join(os.path.dirname(__file__), ICONDIR)
            else: # frozen (added by Prabhu, I think?)
                _icondir = os.path.join(home, ICONDIR)
        except NameError:
            # this probably means that __file__ didn't exist, and that
            # we're being run directly, in which case we have to use
            # argv[0] and ICONDIR to find the real icondir
            _icondir = os.path.join(os.path.dirname(sys.argv[0]), ICONDIR)
        if os.path.isdir(_icondir):
            ICONDIR = _icondir
        elif not os.path.isdir(ICONDIR):
            raise RuntimeError, "can't find icon directory (%s)" % `ICONDIR`

        self._image_list = wx.ImageList(16,16)
        for i in icon_map.values():
            self._image_list.Add(wx.Bitmap(os.path.join(ICONDIR, i + ".xpm"),
                                          wx.BITMAP_TYPE_XPM))
        self._tree_ctrl.SetImageList(self._image_list)

        # do initial population of tree
        self.refresh()

    def refresh (self, event=None):
        """Re-calculates the tree.

        If the pipeline has changed, this can be called to extract a new
        pipeline.
        """
        self.clear()

        if self._objs == None or len(self._objs) == 0:
            if self.renwin == None:
                ConfigVtkObj.print_err('Undefined renderwindow AND objects. '
                                       'Either or both must be defined.')
            else:
                rw_idx = icon_map.values().index(icon_map['RenderWindow'])
                self._root = self._tree_ctrl.AddRoot(text="RenderWindow",
                                                     image=rw_idx)
                self._tree_ctrl.SetPyData(self._root, self.renwin)
                recursively_add_children(self._tree_ctrl, self._root)
        else:
            im_idx = icon_map.values().index(icon_map['Python'])
            self._root = self._tree_ctrl.AddRoot(text="Root",
                                                 image=im_idx)
            self._tree_ctrl.SetPyData(self._root, None)
            
            for i in self._objs:
                # we should probably do a stricter check
                if hasattr(i, 'GetClassName'):
                    icon = get_icon(i)
                    img_idx = icon_map.values().index(icon[2])
                    if icon[0]:
                        text = "%s (%s)" % (icon[0],i.GetClassName())
                    else:
                        text = i.GetClassName()
                    ai = self._tree_ctrl.AppendItem(parent=self._root,
                                                    text=text, image=img_idx)
                    self._tree_ctrl.SetPyData(ai, i)
                    recursively_add_children(self._tree_ctrl, ai)
                
        self._tree_ctrl.Expand(self._root)

    def show(self):
        """Make the window visible.

        After the vtkPipeline has been instantiated, show() must be called
        to make it visible.  In addition, if the user closes the window, it
        can be made visible again by calling show().  These symantics have
        been chosen to facilitate persistent vtkPipelines.
        """
        self._frame.Show(True)
        # make sure the window comes to the top; this is usually not
        # needed right after creation, but show() often gets called because
        # the window was hidden and  needs to appear
        self._frame.Raise()

    def hide(self):
        """Make the window invisible.

        This is called when the user closes the window.
        """
        self._frame.Show(false)

    def clear (self):
        self._tree_ctrl.DeleteAllItems()

    def close(self, event=None):
        """This will destroy the frame/window and make sure that bindings
        to vtk objects are deleted so that VTK reference counts can be
        decremented.

        Make use of this method if you really want to destroy the window and
        don't just want to make it invisible.
        """

        # clean out the tree
        self.clear()
        # close all ConfigVtkObjs
        for cvo in self._config_vtk_objs.values():
            cvo.close()
        # now make sure the list dies
        self._config_vtk_objs.clear()
        # and finally take care of our UI
        self._frame.Destroy()

    def item_activate_cb(self, tree_event):
        """Callback for activation (double clicking) of tree node.
        
        A ConfigVtkObj will be created for the pertinent vtk_obj if one
        hasn't been created already.  In the latter case, the previously
        created ConfigVtkObj will simply be show()n.

        When the vtkFrame self._frame is destroyed (by calling the close()
        method of the relevant vtkPipeline instance), all the ConfigVtkObjs
        will also be destroyed.
        """
        obj = self._tree_ctrl.GetPyData(tree_event.GetItem())
        if hasattr(obj, 'GetClassName'):
            if not self._config_vtk_objs.has_key(obj):
                cvo = ConfigVtkObj.ConfigVtkObj(self._frame,
                                                self.renwin, obj)
                                                
                if hasattr(self.renwin, 'Render'):
                    # well, if we have a renwin, we might as well
                    # use its update method
                    cvo.set_update_method(self.renwin.Render())
                    
                self._config_vtk_objs[obj] = cvo

            # FIXME: we might want to update the renwin
            self._config_vtk_objs[obj].show()

def main ():
    # example code...
    import vtkpython
    from vtk.wx.VTKRenderWindow import VTKRenderWindow
    
    cone = vtkpython.vtkConeSource()
    cone.SetResolution(8)
    transform = vtkpython.vtkTransformFilter ()
    transform.SetInput ( cone.GetOutput() )
    transform.SetTransform ( vtkpython.vtkTransform() )
    coneMapper = vtkpython.vtkPolyDataMapper()
    coneMapper.SetInput(transform.GetOutput())
    l = vtkpython.vtkLookupTable ()
    coneMapper.SetLookupTable (l)
    coneActor = vtkpython.vtkActor()
    coneActor.SetMapper(coneMapper)    
    axes = vtkpython.vtkCubeAxesActor2D ()

    app = wx.PySimpleApp()
    frame = wx.Frame(None, -1, "wx.RenderWindow", size=wx.Size(400,400))
    wid = wx.VTKRenderWindow(frame, -1)

    ren = vtkpython.vtkRenderer()
    renWin = wid.GetRenderWindow()
    renWin.AddRenderer(ren)
    renWin.SetSize(300,300)
    ren.AddActor (coneActor)
    ren.AddActor (axes)
    axes.SetCamera (ren.GetActiveCamera ())
    renWin.Render ()

    debug ("Starting VTK Pipeline Browser...")
    pipe = vtkPipelineBrowser (frame, renWin)
    pipe.show()

    pipe_segment = vtkPipelineBrowser(frame, renWin, (coneActor, axes))
    pipe_segment.show()

    app.MainLoop()

if __name__ == "__main__":
    main ()
