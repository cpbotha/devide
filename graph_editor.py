import Tix

def coords_to_ltriangle(x, y):
    return (x, y, x - 6, y - 3, x - 6, y + 3)

def coords_to_rtriangle(x, y):
    return (x+6, y, x, y - 3, x, y + 3)

class glyph:
    def __init__(self, graph_editor, canvas, coords, name, inputs, outputs):
	self.graph_editor = graph_editor
	self.coords = coords
	self.canvas = canvas
	self.coords_to_rcoords()
	
	# we use this when dragging outputs
	self.cur_output_line = None

	self.inputs = []
	for cur_input in inputs:
	    self.inputs.append(canvas.create_polygon(coords_to_ltriangle(self.rcoords[0], self.rcoords[1] + len(self.inputs)*7)))
	    

	self.outputs = []
	for cur_output in outputs:
	    self.outputs.append(canvas.create_polygon(coords_to_rtriangle(self.rcoords[2], self.rcoords[1])))
	    # but we do want to catch drags from the output triangles (and we need to tell graph_editor
	    # about this somehow)
	    canvas.tag_bind(self.outputs[-1], "<B1-Motion>", lambda event, item=self.outputs[-1], s=self: s.output_drag_cb(event, item))
	    canvas.tag_bind(self.outputs[-1], "<ButtonRelease-1>", self.output_release_cb)
	    
	self.rectangle = canvas.create_rectangle(self.rcoords, fill="gray80")
	self.text = canvas.create_text(self.coords[0], self.coords[1], text=name, width=75)
	# bind move handler to text and rectangle (the glyph can move itself)
	canvas.tag_bind(self.rectangle, "<B1-Motion>", self.move_cb)
	canvas.tag_bind(self.text, "<B1-Motion>", self.move_cb)	
	
    def coords_to_rcoords(self):
	self.rcoords = (self.coords[0]-40, self.coords[1]-10, self.coords[0]+40, self.coords[1]+10) # tuple
	
    def output_drag_cb(self, event, item):
	if not self.cur_output_line:
	    self.cur_output_line = self.canvas.create_line(self.canvas.coords(item), event.x, event.y)
	else: 
	    self.canvas.coords(self.cur_output_line, self.canvas.coords(item)[0], self.canvas.coords(item)[1], event.x, event.y)
	    
    def output_release_cb(self, event):
	item = self.canvas.find_withtag(Tix.CURRENT)
	print item
	    
    def input_enter_cb(self, event):
	print "entered"
		
    def move_cb(self, event):
	self.move((event.x, event.y))
		
    def move(self, to_coords):
	# do I really have to do it this way?
        dx = to_coords[0] - self.coords[0]
	dy = to_coords[1] - self.coords[1]	
	self.coords = to_coords
	self.coords_to_rcoords()
	self.canvas.move(self.text, dx, dy)
	self.canvas.move(self.rectangle, dx, dy)
	for cur_input in self.inputs:
	    self.canvas.move(cur_input, dx, dy)
	for cur_output in self.outputs:
	    self.canvas.move(cur_output, dx, dy)	    
	
    def contains(self, x, y):
	#return x > self.rcoords[0]-6 and x < self.rcoords[2]+6 and y > self.rcoords[1]-3 and y < self.rcoords[3]+3
	return x > self.rcoords[0] and x < self.rcoords[2] and y > self.rcoords[1] and y < self.rcoords[3]

class graph_editor:
    def __init__(self, dscas3_main):
	self.dscas3_main = dscas3_main

	self.glyphs = []
	self.drag_glyph = None
    
	# create window for the glyph editor
	self.window = Tix.Toplevel()
	
	# create canvas for drawing glyph layouts on
	self.canvas = Tix.Canvas(self.window)
	self.canvas.bind("<Button-1>", self.canvas_b1click_cb)
	self.canvas.bind("<ButtonRelease-1>", self.canvas_b1release_cb)
	#self.canvas.bind("<B1-Motion>", self.canvas_b1drag_cb)
	self.canvas.pack(side=Tix.TOP, expand=1, fill=Tix.BOTH)
	
    def canvas_b1click_cb(self, event):
	item = self.canvas.find_withtag(Tix.CURRENT)
	print item
	item_type = self.canvas.type(item)
	# we only create a glyph if we don't click on anything already in the canvas
	if item_type == None:
	    self.glyphs.append(glyph(self, self.canvas, (event.x, event.y),
	    "Hello World", ("vtkStructuredPoints", "vtkImageData"), ("vtkStructuredPoints")))
	
    def canvas_b1release_cb(self, event):
	item = self.canvas.find_withtag(Tix.CURRENT)
	print "ge release %s" % item
	# now query all glyphs as to who has this item as input
	# and make sure that a connection drag was in progress

    def canvas_b1drag_cb(self, event):
	print "bish"
	    
