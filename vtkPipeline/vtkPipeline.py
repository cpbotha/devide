#!/usr/bin/env python
#
# $Id: vtkPipeline.py,v 1.1 2002/02/16 00:33:45 cpbotha Exp $
#
# This python program/module creates a graphical VTK pipeline browser.  
# The objects in the pipeline can be configured.
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

"""  This python program/module creates a graphical VTK pipeline
browser.   The pipeline tree is made using the TreeWidget from IDLE.
The objects in the pipeline can be configured.  The configuration is
done by using the ConfigVtkObj class.
"""

import string, re, types, Tkinter
import TreeWidget
import ConfigVtkObj

# set this to 1 if you want to see debugging messages - very useful if
# you have problems
DEBUG=0
def debug (msg):
    if DEBUG:
	print msg

# A hack to prevent vtkTransform.GetInverse() infinite loops
last_transform = 0

class vtkTreeNode (TreeWidget.TreeNode):

    """Overloaded TreeNode to do somethings I want.  Can do it better,
    but this works."""

    def __del__ (self):
        debug ("vtkTreeNode.__del__")

    def flip(self, event=None):
        if self.state == 'expanded':
	    # changed by prabhu to stop unnecessary collapses
	    #self.collapse()
	    pass
        else:
            self.expand()
        self.item.OnDoubleClick()
        return "break"

    def get_all_children (self):
	"Recursively gets all the children of all nodes."
	self.get_children ()	
	for child in self.children:
	    child.get_all_children ()

    def get_children (self):
	"This is used to get all the children to expand the tree."
	if not self.children:
	    sublist = self.item._GetSubList ()
	    if not sublist:
		return None
	    for item in sublist:
		child = vtkTreeNode (self.canvas, self, item)
		self.children.append (child)	

    def expand_all (self):
	"This is used to expand all the children nodes."
	self.expand ()
	for child in self.children:
	    child.expand_all ()


icon_map = {'RenderWindow': 'renwin', 'Renderer': 'ren',
            'Actor': 'actor', 'Light': 'light', 'Camera': 'camera',
            'Mapper': 'process', 'Property': 'file',
	    'Coordinate': 'coord', 'Source': 'data', 
	    'LookupTable': 'colormap', 'Reader': 'data'}

def get_icon (vtk_obj):
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
		if string.find (t, "vtkPropC") > -1:
		    prop = 1
		for i in range (0, n):
		    if prop:
			obj = col.GetNextProp ()
		    else:
			obj = col.GetNextItem ()
		    icon = get_icon (obj)
		    vtk_objs.append (["%s%d"%(icon[0], i), obj, icon[2]])
	    else:
		obj = eval ("vtk_obj.Get%s ()"%method[0])
		vtk_objs.append (get_icon (obj))

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
            vtk_objs.append (icon)
    
    return vtk_objs


class vtkTreeItem (TreeWidget.TreeItem):

    """A general VTK Tree item.  The parent TreeItem class is defined
    in TreeWidget.py"""

    def __init__ (self, name, obj, icon="question", renwin=None):
	"The icon variable corresponds to a file in the Icons dir."
	# renwin arg is to enable Render calls while doing config
	self.renwin = renwin
	self.icon = icon
	self.obj = obj	
	if obj:
	    if name:
		self.name = "%s (%s)"%(name, obj.GetClassName ())
	    else:
		self.name = "%s"%obj.GetClassName ()
	    self.expandable = 1
	else:
	    self.name = name
	    self.expandable = 0

    def __del__ (self):
        debug ("vtkTreeItem.__del__")

    def GetText (self):
	return self.name

    def IsEditable (self):
	return 0

    def GetIconName (self):
	return self.icon

    def IsExpandable (self):
	return self.expandable

    def GetSubList (self):
	items = get_vtk_objs (self.obj)
	children = []
	for item in items:
	    item.append (self.renwin)
	    children.append (apply (vtkTreeItem, item))
	return children

    def OnDoubleClick (self):
	conf = ConfigVtkObj.ConfigVtkObj (self.renwin)
	conf.configure (None, self.obj)


class DummyTreeItem (TreeWidget.TreeItem):
    
    """ This is a dummy tree item that is used only for the
    vtkPipelineSegmentBrowser.  It is used so that you can visualize a
    segment of the pipeline starting from anywhere in the actual
    pipeline."""

    def __init__ (self, objs, renwin=None):
	# renwin arg is to enable Render calls while doing config
	self.renwin = renwin
	self.icon = "tk"
	self.objs = objs	

    def __del__ (self):
        debug ("DummyTreeItem.__del__")

    def GetText (self):
	return "..."

    def IsEditable (self):
	return 0

    def GetIconName (self):
	return self.icon

    def IsExpandable (self):
	return 1

    def GetSubList (self):
        children = []
        if (type (self.objs) is types.ListType) or \
           (type (self.objs) == types.TupleType):
            for obj in self.objs:
                l = get_icon (obj)
                l.append (self.renwin)
                children.append (apply (vtkTreeItem, l))
        else:
            l = get_icon (self.objs)
            l.append (self.renwin)
            children.append (apply (vtkTreeItem, l))
	return children

    def OnDoubleClick (self):
        pass


class vtkPipelineBrowser:
    "Browses the VTK pipleline given a vtkRenderWindow."

    def __init__ (self, master, renwin):
	"renwin is an instance of some vtkRenderWindow."
	self.renwin = renwin
	self.root = Tkinter.Toplevel (master)
	self.root.title ("VTK Pipeline Browser")
	self.root.focus_set ()
        self.root.protocol ("WM_DELETE_WINDOW", self.destroy)
	frame = Tkinter.Frame (self.root)
	frame.pack (side='top', expand=1, fill='both')
	self.sc = TreeWidget.ScrolledCanvas (frame, bg="white", 
                                             highlightthickness=0,
                                             takefocus=1)
	self.sc.frame.pack (expand=1, fill='both')
	f = Tkinter.Frame (self.root)
	f.pack (side='bottom')
	refr = Tkinter.Button (f, text="Refresh", underline=2, 
                               command=self.refresh)
	refr.grid (row=0, column=0, sticky='ew')
	ex_all = Tkinter.Button (f, text="Expand all", underline=0, 
                                 command=self.expand_all)
	ex_all.grid (row=0, column=1, sticky='ew')
	quit = Tkinter.Button (f, text="Close", underline=0,
                               command=self.quit)
	quit.grid (row=0, column=2, sticky='ew')
	
	self.root.bind ("<Alt-f>", self.refresh)
	self.root.bind ("<Alt-e>", self.expand_all)
	self.root.bind ("<Alt-c>", self.quit)

        self.root_node = None

    def browse (self):
	"Display the tree and interact with the user."
        self.clear ()
	self.root_item = vtkTreeItem ("RenderWindow", self.renwin, 
				      "renwin", self.renwin)
	self.root_node = vtkTreeNode (self.sc.canvas, None, self.root_item)
	self.root_node.get_all_children ()
	self.root_node.expand ()

    def refresh (self, event=None):
        self.browse ()

    def expand_all (self, event=None):
	"Expand all nodes from the root down."
	self.root_node.expand_all ()

    def clear (self):
        if self.root_node:
            self.root_node.destroy ()        

    def destroy (self, event=None):
        self.quit (event)

    def quit (self, event=None):
	"Exit the browser."
        self.clear ()
        self.sc.canvas.destroy ()
	del self.sc
	del self.root_item
	del self.root_node
	self.root.destroy ()
        
    def isdestroyed ( self ):
        return not 'sc' in dir ( self );


class vtkPipelineSegmentBrowser (Tkinter.Frame):

    """Creates a frame containing a segment of the VTK pipleline given
    a set of VTK objects."""

    def __init__ (self, master, objs, renwin=None):
	"renwin is an instance of some vtkRenderWindow."
        Tkinter.Frame.__init__ (self, master)
	self.renwin = renwin
	self.frame = Tkinter.Frame (self)
	self.frame.pack (side='top', expand=1, fill='both')
	self.sc = TreeWidget.ScrolledCanvas (self.frame, bg="white", 
                                             highlightthickness=0,
                                             takefocus=1,
                                             width=200, height=150)
	self.sc.frame.pack (side='top', expand=1, fill='both')
	f = Tkinter.Frame (self.frame)
	f.pack (side='bottom' )
	refr = Tkinter.Button (f, text="Refresh", underline=2, 
                               command=self.browse)
	refr.grid (row=0, column=0, sticky='ew')
	ex_all = Tkinter.Button (f, text="Expand all", underline=0, 
                                 command=self.expand_all)
	ex_all.grid (row=0, column=1, sticky='ew')
	
	self.sc.canvas.bind ("<Alt-f>", self.browse)
	self.sc.canvas.bind ("<Alt-e>", self.expand_all)

        self.root_node = None
        self.root_item = None
        self.objs = objs
        self.browse ()

    def browse (self, event=None):
	"Display the tree and interact with the user."
        self.clear ()
        self.root_item = DummyTreeItem (self.objs, self.renwin)
        self.root_node = vtkTreeNode (self.sc.canvas, None, self.root_item)
        self.root_node.get_all_children ()
        self.root_node.expand ()

    def expand_all (self, event=None):
	"Expand all nodes from the root down."
	self.root_node.expand_all ()

    def clear (self):
        if self.root_node:
            self.root_node.destroy ()
        
    def destroy (self, event=None):
	"Close the browser."
        self.clear ()
        self.sc.canvas.destroy ()
	del self.sc
	del self.root_item
	del self.root_node
	self.frame.destroy ()

    def isdestroyed ( self ):
        return not 'sc' in dir (self)


def main ():
    import vtkpython, vtkRenderWidget
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

    root = Tkinter.Tk ()
    wid = vtkRenderWidget.vtkTkRenderWidget (root, width=500, height=500)
    wid.pack (expand='true', fill='both')
    wid.bind ("<KeyPress-q>",
              lambda e=None: e.widget.winfo_toplevel().destroy())

    ren = vtkpython.vtkRenderer()
    renWin = wid.GetRenderWindow()
    renWin.AddRenderer(ren)
    renWin.SetSize(300,300)
    ren.AddActor (coneActor)
    ren.AddActor (axes)
    axes.SetCamera (ren.GetActiveCamera ())
    renWin.Render ()

    debug ("Starting VTK Pipeline Browser...")
    pipe = vtkPipelineBrowser (root, renWin)
    pipe.browse ()

    top = Tkinter.Toplevel (root)
    top.title ("VTK Pipeline Segment Browser")
    pipe_segment = vtkPipelineSegmentBrowser (top, (coneActor, axes),
                                              renWin)
    pipe_segment.pack (side='top', expand = 1, fill = 'both' )
    top.protocol ("WM_DELETE_WINDOW", top.destroy)
    root.mainloop ()

if __name__ == "__main__":
    main ()
