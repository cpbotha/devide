import sys, re
import Tkinter
from Tkconstants import *
import tkMessageBox
import Pmw
import external.Tree

def coords_to_ltriangle(x, y):
    return (x, y, x - 6, y - 3, x - 6, y + 3)

def coords_to_rtriangle(x, y):
    return (x+6, y, x, y - 3, x, y + 3)

# ----------------------------------------------------------------------------
# glyph class
# ----------------------------------------------------------------------------

class glyph:
    def __init__(self, graph_editor, canvas, coords, module_instance):
	self.module_instance = module_instance

	# extract the module name from the __class__ attribute of the passed instance
	sres = re.search(".*\.(.*)", str(module_instance.__class__))
	if sres.group(1):
	    self.module_name = sres.group(1)
	else:
	    self.module_name = "UNKNOWN"
	
	self.graph_editor = graph_editor
	self.coords = coords
	self.canvas = canvas
	self.coords_to_rcoords()
	
	self.output_lines = []

	self.inputs = [] # list consisting of tuples (triangle_item, connecting line, connecting glyph)
	for cur_input_type in module_instance.get_input_descriptions():
	    self.inputs.append({'item': canvas.create_polygon(coords_to_ltriangle(self.rcoords[0], self.rcoords[1] + len(self.inputs)*7)),
	    'line': None, 'glyph': None})
	    canvas.tag_bind(self.inputs[-1]['item'], "<Enter>", self.input_enter_cb)
	    canvas.tag_bind(self.inputs[-1]['item'], "<Button-1>", self.input_click_cb)
	    
	self.outputs = []
	for cur_output_type in module_instance.get_output_descriptions():
	    self.outputs.append(canvas.create_polygon(coords_to_rtriangle(self.rcoords[2], self.rcoords[1])))
	    canvas.tag_bind(self.outputs[-1], "<Enter>", self.output_enter_cb)
	    canvas.tag_bind(self.outputs[-1], "<Button-1>", self.output_click_cb)
	    
	self.rectangle = canvas.create_rectangle(self.rcoords, fill="gray80")
	self.text = canvas.create_text(self.coords[0], self.coords[1], text=self.module_name, width=115)
	# add click handlers for rectangle and text so we can delete the glyph
	canvas.tag_bind(self.rectangle, "<Button-1>", self.b1click_cb)
	canvas.tag_bind(self.text, "<Button-1>", self.b1click_cb)
	# bind move handler to text and rectangle (the glyph can move itself)
	canvas.tag_bind(self.rectangle, "<B1-Motion>", self.move_cb)
	canvas.tag_bind(self.text, "<B1-Motion>", self.move_cb)
	
    def __del__(self):
	print "in glyph.__del__()"
	
    def close(self):
	print "in glyph.close()"
	# take care of our reference to the module
	del self.module_instance
	# remove ourselves from the canvas
	self.canvas.delete(self.text)
	self.canvas.delete(self.rectangle)
	for cur_input in self.inputs:
	    self.canvas.delete(cur_input['item'])
	for cur_output in self.outputs:
	    self.canvas.delete(cur_output)
	#for cur_output_line in self.output_lines:
	#    self.canvas.delete(cur_output_line)
	for cur_input in self.inputs:
	    if cur_input['line']:
		self.canvas.delete(cur_input['line'])
	
    def accept_connection(self, from_glyph, input_line, input_idx):
	self.inputs[input_idx]['line'] = input_line
	self.inputs[input_idx]['glyph'] = from_glyph
	
    def coords_to_rcoords(self):
	self.rcoords = (self.coords[0]-60, self.coords[1]-15, self.coords[0]+60, self.coords[1]+15) # tuple
	
    def connect_to(self, output_idx, other_glyph, input_idx):
	if not other_glyph.is_connected_on(input_idx):
	    otri_coords = self.get_otri_coords(output_idx)
	    itri_coords = other_glyph.get_itri_coords(input_idx)
	    self.output_lines.append(self.canvas.create_line(otri_coords[0], otri_coords[1], itri_coords[2], itri_coords[1]))
	    other_glyph.accept_connection(self, self.output_lines[-1], input_idx)
	    
    def remove_line(self, item):
	self.output_lines.remove(item)
	    
    def disconnect_from(self, output_glyph, input_idx):
	# first remove record of input glyph
	self.inputs[input_idx]['glyph'] = None
	# remove the actual line from the canvas
	self.canvas.delete(self.inputs[input_idx]['line'])
	# tell the output glyph that the line should be removed from its list
	output_glyph.remove_line(self.inputs[input_idx]['line'])
	# finally remove it from our own list
	self.inputs[input_idx]['line'] = None
	    
    def find_input_idx(self, item):
	idx = -1
	for i in self.inputs:
	    if i['item'] == item:
		idx = self.inputs.index(i)
		break
	return idx
    
    def get_otri_coords(self, output_idx):
	return self.canvas.coords(self.outputs[output_idx])
	
    def get_itri_coords(self, input_idx):
	return self.canvas.coords(self.inputs[input_idx]['item'])
    
    def get_module_instance(self):
	return self.module_instance
    
    def find_inputs(self, output_glyph):
	"Finds on which inputs we're getting input from output_glyph."
	input_idxs = []
	for i in self.inputs:
	    if i['glyph'] == output_glyph:
		input_idxs.append(self.inputs.index(i))
	return input_idxs
    
    def is_connected_on(self, input_idx):
	return self.inputs[input_idx]['glyph']
    
    def move(self, to_coords):
	# do I really have to do it this way?
        dx = to_coords[0] - self.coords[0]
	dy = to_coords[1] - self.coords[1]	
	self.coords = to_coords
	self.coords_to_rcoords()
	self.canvas.move(self.text, dx, dy)
	self.canvas.move(self.rectangle, dx, dy)
	for cur_input in self.inputs:
	    self.canvas.move(cur_input['item'], dx, dy)
	for cur_output in self.outputs:
	    self.canvas.move(cur_output, dx, dy)
	# now move all the output lines
	for cur_output_line in self.output_lines:
	    coords = self.canvas.coords(cur_output_line)
	    coords[0] += dx
	    coords[1] += dy
	    # is there not a better way to break the coords list up?
	    self.canvas.coords(cur_output_line, coords[0], coords[1], coords[2], coords[3])
	# and the input lines
	for cur_input in self.inputs:
	    if cur_input['line']:
		coords = self.canvas.coords(cur_input['line'])
		coords[2] += dx
		coords[3] += dy
		# is there not a better way to break the coords list up?
		self.canvas.coords(cur_input['line'], coords[0], coords[1], coords[2], coords[3])
		
    def b1click_cb(self, event):
	if self.graph_editor.get_mode() == 'Delete':
	    self.graph_editor.delete_glyph(self)
	elif self.graph_editor.get_mode() == 'View':
	    self.graph_editor.view_glyph(self)
	
    def output_drag_cb(self, event, item):
	if not self.cur_output_line:
	    self.cur_output_line = self.canvas.create_line(self.canvas.coords(item), event.x, event.y)
	else: 
	    self.canvas.coords(self.cur_output_line, self.canvas.coords(item)[0], self.canvas.coords(item)[1], event.x, event.y)
	    
    def input_enter_cb(self, event):
	item = self.canvas.find_withtag(CURRENT)
	if len(item) == 1:
	    idx = self.find_input_idx(item[0])
	    if (idx > -1):
		self.graph_editor.set_status("Input " + self.get_module_instance().get_input_descriptions()[idx])
	
    def input_click_cb(self, event):
	item = self.canvas.find_withtag(CURRENT)
	if len(item) == 1:
	    idx = self.find_input_idx(item[0])
	    if (idx > -1):
		if self.graph_editor.get_mode() == 'Edit':
		    self.graph_editor.glyph_input_clicked(self, idx)
		elif self.graph_editor.get_mode() == 'Delete':
		    self.graph_editor.disconnect_glyphs(self.inputs[idx]['glyph'], self, idx)
	elif (len(item) > 1):
	    print "This shouldn't happen!!"
    
    def output_enter_cb(self, event):
	item = self.canvas.find_withtag(CURRENT)
	if len(item) == 1:
	    idx = self.outputs.index(item[0])
	    if (idx > -1):
		self.graph_editor.set_status("Output " + self.get_module_instance().get_output_descriptions()[idx])
	
	
    def output_click_cb(self, event):
	item = self.canvas.find_withtag(CURRENT)
	if (len(item) == 1):
	    # find the item
	    idx = self.outputs.index(item[0])
	    self.graph_editor.glyph_output_clicked(self, idx)
	elif (len(item) > 1):
	    print "This shouldn't happen!!"

		
    def move_cb(self, event):
	self.move((event.x, event.y))
		
	
    def contains(self, x, y):
	#return x > self.rcoords[0]-6 and x < self.rcoords[2]+6 and y > self.rcoords[1]-3 and y < self.rcoords[3]+3
	return x > self.rcoords[0] and x < self.rcoords[2] and y > self.rcoords[1] and y < self.rcoords[3]

# ----------------------------------------------------------------------------
# graph_editor class
# ----------------------------------------------------------------------------

class my_tree_node(external.Tree.Node):
    def __init__(self, *args, **kw_args):
	# call superclass (actually, I have no idea about this (self,)+args!)
	apply(external.Tree.Node.__init__, (self,)+args, kw_args)
	self.widget.tag_bind(self.symbol, '<1>', lambda e, self=self: self.widget.move_cursor(self))
	self.widget.tag_bind(self.label, '<1>', lambda e, self=self: self.widget.move_cursor(self))
	self.widget.tag_bind(self.label, '<Double-1>', lambda e, self=self: self.toggle_state()) # e is the event parameter that gets passed
	
class graph_editor:
    def __init__(self, dscas3_main):
	self.dscas3_main = dscas3_main

	self.glyphs = []
	self.drag_glyph = None
	# dictionaries, wow
	self.conn_ip = {'glyph0': None, 'out_idx': -1, 'glyph1': None, 'in_idx': -1}
    
	# create window for the glyph editor
	self.window = Tkinter.Toplevel()
	# FIXME: we need to set some better close method
	self.window.title("dscas3 graph editor")
	self.window.protocol("WM_DELETE_WINDOW", self.window.destroy)
	
	# sunken label with border width 1
        self.status = Tkinter.Label(self.window, relief=SUNKEN, bd=1, anchor=W)
        self.status.pack(side=BOTTOM, fill=X, padx=2, pady=1)
	self.status['text'] = "Welcome to the Graph Editor"
	
	tree_frame = Tkinter.Frame(self.window)
	tree_frame.pack(side=LEFT, fill=Y, expand=0)

	self.module_tree = external.Tree.Tree(width=140, master=tree_frame, root_id='.', root_label='Modules', get_contents_callback=self.get_tree_node_contents, node_class=my_tree_node)
	self.module_tree.root.expand()

	# let's just create and pack this first
	sb=Tkinter.Scrollbar(tree_frame, orient=HORIZONTAL)
	sb.pack(side=BOTTOM, fill=X)
	self.module_tree.configure(xscrollcommand=sb.set)
	sb.configure(command=self.module_tree.xview)
	
	# then the module_tree
	self.module_tree.pack(side=LEFT, fill=Y, expand=0)
	
	# and then the vertical scrollbar
	sb=Tkinter.Scrollbar(tree_frame)
	sb.pack(side=LEFT, fill=Y)
	self.module_tree.configure(yscrollcommand=sb.set)
	sb.configure(command=self.module_tree.yview)
	
	# create canvas for drawing glyph layouts on
	self.canvas = Tkinter.Canvas(self.window, background="white")
	self.canvas.bind("<Button-1>", self.canvas_b1click_cb)
	self.canvas.pack(side=LEFT, expand=1, fill=BOTH)
	
	# frame
	self.command_frame = Tkinter.Frame(self.window)
	self.command_frame.pack(side=LEFT, fill=BOTH)
	
	# then some command buttons
	self.command_frame.mode_select = Pmw.RadioSelect(self.command_frame, buttontype='radiobutton', orient='vertical')

	self.command_frame.mode_select.add('Edit')
	self.command_frame.mode_select.add('Delete')
	self.command_frame.mode_select.add('View')
	
	self.command_frame.mode_select.invoke('Edit')
	
	self.command_frame.mode_select.pack(side=TOP)
	
    def get_tree_node_contents(self, node):
	if node.full_id() == ('.',):
	    node.widget.add_node('Readers', 'rdr', 1)
	    node.widget.add_node('Writers', 'wrt', 1)
	    node.widget.add_node('Viewers', 'vwr', 1)
	    node.widget.add_node('Filters', 'flt', 1)
	else:
	    # we're in one of the sublists, and this has just been opened
	    # we should get the module_manager to rescan for new modules
	    # (this is not working yet)
	    self.dscas3_main.get_module_manager().scan_modules()
	    # compile regular expresion for something like: ".*rdr$"
	    cre = re.compile(".*%s$" % (node.full_id()[1]), re.I)
	    for i in self.dscas3_main.get_module_manager().get_module_list():
		if cre.search(i):
		    node.widget.add_node(name=i, id=i, flag=0)
		    
    def get_currently_selected_module_type(self):
	tree_node = self.module_tree.cursor_node(None)
	print tree_node.full_id()
	# it can only be a module if it's this deep in the tree, mmkay?
	if tree_node and len(tree_node.full_id()) == 3:
	    return tree_node.full_id()[2]
	else:
	    return None
	
    def create_glyph(self, x, y):
	# see what's selected in the tree (make sure it's not a section heading)
	module_type = self.get_currently_selected_module_type()
	if module_type:
	    temp_module = self.dscas3_main.get_module_manager().create_module(module_type)
	    if temp_module:
		self.glyphs.append(glyph(self, self.canvas, (x,y),
		temp_module))
		    
    def delete_glyph(self, glyph):
        try:
	    # iterate through all glyphs, finding out whether this glyph is an
	    # input glyph for it
	    for cur_input_glyph in self.glyphs:
		if cur_input_glyph != glyph: # hmmm, can I do this?
		    # if our glyph supplies output to cur_input_glyph, this will find
		    # all the input indexes on cur_input_glyph
		    input_idxs = cur_input_glyph.find_inputs(glyph)
		    for cur_idx in input_idxs:
			# "glyph" is the output glyph, disconnect the glyph
			print "disconnecting %s from %s, index %s" % (glyph.get_module_instance().__class__,
			cur_input_glyph.get_module_instance().__class__, cur_idx)
			self.disconnect_glyphs(glyph, cur_input_glyph, cur_idx)
	    # now get dscas3 to delete the actual module
	    self.dscas3_main.get_module_manager().delete_module(glyph.get_module_instance())
	    # then de-init the glyph object
	    glyph.close()
	    # then remove and delete the reference to it from the glyphs list
	    del self.glyphs[self.glyphs.index(glyph)]
	except Exception, e:
	    tkMessageBox.showerror("Destruction error", "Unable to destroy object: %s" % str(e))
	    print sys.exc_info()
	    
    def view_glyph(self, glyph):
	# we should probably thunk this through to dscas3_main?
	glyph.get_module_instance().view()
	
    def canvas_b1click_cb(self, event):
	if self.get_mode() == 'Edit':
	    item = self.canvas.find_withtag(CURRENT)
	    item_type = self.canvas.type(item)
	    # we only create a glyph if we don't click on anything already in the canvas
	    if item_type == None:
		self.create_glyph(event.x, event.y)
	
    def glyph_input_clicked(self, glyph, idx):
	if self.conn_ip['glyph0']:
	    self.conn_ip['glyph1'] = glyph
	    self.conn_ip['in_idx'] = idx
	    self.connect_glyphs()
	
    def glyph_output_clicked(self, glyph, idx):	
	# cancel any pending connections, start anew
	self.conn_ip['glyph0'] = glyph
	self.conn_ip['out_idx'] = idx
	
    def connect_glyphs(self):
	"""This will ask the main module whether the glyphs setup in 
	self.conn_ip can be connected. If so, it will connect them graphically
	and also the objects which they actually represent."""
	try:
	    # do the actual connection (this should actually go to the module_manager)
	    self.dscas3_main.get_module_manager().connect_modules(self.conn_ip['glyph0'].get_module_instance(), self.conn_ip['out_idx'],
	    self.conn_ip['glyph1'].get_module_instance(), self.conn_ip['in_idx'])
	    # tell the glyphs to connect to each other (and store the line handles, aaaaaai!)
	    self.conn_ip['glyph0'].connect_to(self.conn_ip['out_idx'], self.conn_ip['glyph1'], self.conn_ip['in_idx'])
	    # we only have to do this bit for new connections to work again
	    self.conn_ip['glyph0'] = None
	except Exception, e:
	    tkMessageBox.showerror("Connect error", "Could not connect modules: %s" % (str(e)))
	    print sys.exc_info()	    
	
    def disconnect_glyphs(self, output_glyph, input_glyph, input_idx):
	"""This will ask the main module whether the glyphs in question
	may disconnect the requested inputs/outputs.  If allowed, the
	situation in the graph editor will be adapted."""
	self.dscas3_main.get_module_manager().disconnect_modules(input_glyph.get_module_instance(), input_idx)
	input_glyph.disconnect_from(output_glyph, input_idx)
	
    def get_mode(self):
	return self.command_frame.mode_select.getcurselection()
	
    def set_status(self, text):
	self.status['text'] = text
	
	
