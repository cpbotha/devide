import Tix

def coords_to_ltriangle(x, y):
    return (x, y, x - 6, y - 3, x - 6, y + 3)

def coords_to_rtriangle(x, y):
    return (x+6, y, x, y - 3, x, y + 3)

class glyph:
    def __init__(self, canvas, coords, name, inputs, outputs):
	self.coords = coords
	self.canvas = canvas
	self.coords_to_rcoords()
	self.rectangle = canvas.create_rectangle(self.rcoords, fill="gray80")
	self.inputs = []
	for cur_input in inputs:
	    self.inputs.append(canvas.create_polygon(coords_to_ltriangle(self.rcoords[0], self.rcoords[1])))
	self.outputs = []
	for cur_output in outputs:
	    self.outputs.append(canvas.create_polygon(coords_to_rtriangle(self.rcoords[2], self.rcoords[3])))
	self.text = canvas.create_text(self.coords[0], self.coords[1], text=name, width=75)
	
    def coords_to_rcoords(self):
	self.rcoords = (self.coords[0]-40, self.coords[1]-10, self.coords[0]+40, self.coords[1]+10) # tuple
		
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
	return x > self.rcoords[0] and x < self.rcoords[2] and y > self.rcoords[1] and y < self.rcoords[3]

class graph_editor:
    def __init__(self, dscas3_main):
	self.dscas3_main = dscas3_main

	self.glyphs = []
	self.selected_glyph = None
	self.drag_glyph = None
    
	# create window for the glyph editor
	self.window = Tix.Toplevel()
	
	# create canvas for drawing glyph layouts on
	self.canvas = Tix.Canvas(self.window)
	self.canvas.bind("<Button-1>", self.canvas_b1click_cb)
	self.canvas.bind("<ButtonRelease-1>", self.canvas_b1release_cb)
	self.canvas.bind("<B1-Motion>", self.canvas_b1drag_cb)
	self.canvas.pack(side=Tix.TOP, expand=1, fill=Tix.BOTH)
	
    def canvas_b1click_cb(self, event):
	# first check if the clicked point is not in a glyph
	found = 0
	for cur_glyph in self.glyphs:
	    if cur_glyph.contains(event.x, event.y):
		found = 1
		break
	if found:
	    self.selected_glyph = cur_glyph
	else:
	    self.glyphs.append(glyph(self.canvas, (event.x, event.y), 
	    "Hello World", ("vtkStructuredPoints", "vtkImageData"), ("vtkStructuredPoints")))
	    
    def canvas_b1release_cb(self, event):
	self.selected_glyph = None

    def canvas_b1drag_cb(self, event):
	if self.selected_glyph:
	    self.selected_glyph.move((event.x, event.y))
	    
