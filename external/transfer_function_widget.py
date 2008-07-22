# Original code TransferFunctionWidget.py found at
# http://www.siafoo.net/snippet/122 on 20080721
# wxWindows Library License, copyright Stou S. <stou@icapsid.net>

# modified for integration with DeVIDE by Charl P. Botha <cpbotha.net>
#
# * OnSize handler, dynamic sizing (e.g. with sizers).
# * Scalar range can be changed dynamically.
# * Removed all unnecessary self.x and self.y offsetting.
# * Fixed for negative scalar ranges and whatnot.
# * Colour state (defaults, custom colours) is maintained between
#   invocations of the colour dialog.
# * Custom events are signalled for point selections and what not.
#
# more info on DeVIDE: http://visualisation.tudelft.nl/Projects/DeVIDE

import wx
import numpy

# ET is used in here for the CommandEvent
EVT_CUR_PT_CHANGED_ET = wx.NewEventType()
# the EventBinder is used on the outside to bind to this new event
EVT_CUR_PT_CHANGED = wx.PyEventBinder(EVT_CUR_PT_CHANGED_ET, 1)

class TransferPoint(object):
    
    def __init__(self, value, color, alpha, fixed = False):
        self.value = value
        # Color is 0 to 255
        self.color = color
        # Alpha is 0.0 to 1.0
        self.alpha = alpha
    
        if len(color) != 3:
            raise Exception, 'Color should have length of 3'

        self.radius = 5
        self.fixed = fixed

    def __cmp__(self, pt):
        ''' Used by the sort method'''
        if self.value < pt.value: return -1
        elif self.value > pt.value: return 1
        return 0
    
    def get_alpha(self):
        return self.alpha

    def get_rgba(self):
        return [self.color[0], self.color[1], self.color[2], self.alpha]
   

class TransferFunctionWidget(wx.PyWindow):

    def __init__(self, parent, id=wx.ID_ANY, label="", pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.NO_BORDER, 
                 name="TransferFunction"):
        
        wx.PyWindow.__init__(self, parent, id, pos, size,
                style|wx.FULL_REPAINT_ON_RESIZE, name)
        
        # Local Variables
        self.m_BorderLeft = 20
        self.m_BorderUp = 5
        self.m_BorderRight = 5
        self.m_BorderDown = 13

        self.m_GridLines = 10
        self.m_TickSize = 4
        self.m_TickBorder = 2
        self.m_labelFontPt = 10

        # temporary variable.
        minmax = (0.0, 255.0)

        # The transfer points
        self.points = []
        self.points.append(TransferPoint(
            minmax[0], [255, 255, 255], 0, fixed=True))
        self.points.append(TransferPoint(
            minmax[1], [0, 0, 0], 1.0, fixed=True))
        
        self.mouse_down = False
        self.prev_x = 0
        self.prev_y = 0
        self.cur_pt = None

        # we'll use this to maintain colour state
        self.colour_data = None

        # call this for initial setting of size variables
        self._update_size()

        # Bind events
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_SIZE, self.OnSize)

        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnMouseDown)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnMouseDClick)
        self.Bind(wx.EVT_LEFT_UP, self.OnMouseUp)
        self.Bind(wx.EVT_MOTION, self.OnMouseMotion)

    def OnSize(self, event):
        # update all internal variables
        self._update_size()
        # then redraw everything
        #self.Refresh()

    def OnKeyDown(self, event):
        """ Handles the wx.EVT_KEY_DOWN event for CustomCheckBox. """

        if event.GetKeyCode() == wx.WXK_SPACE:
            # The spacebar has been pressed: toggle our state
            self.SendCheckBoxEvent()
            event.Skip()
            return

        event.Skip()
       
    def OnPaint(self, event):
        """ Handles the wx.EVT_PAINT event for CustomCheckBox. """

        dc = wx.BufferedPaintDC(self)
        self.Draw(dc)

    def DrawPoints(self, dc):


        
        x = self.x_from_value(self.points[0].value)
        y = self.y_from_alpha(0.0)
        
        for pt in self.points:
            
            x_c = self.x_from_value(pt.value)
            y_c = self.y_from_alpha(pt.get_alpha())

            dc.SetPen(wx.Pen(wx.Color(0,0,0)))   
            dc.DrawLine(x, y, x_c, y_c)

            if self.cur_pt and self.cur_pt == pt:
                dc.SetBrush(wx.Brush(wx.Color(192,192,192), wx.SOLID))
                dc.SetPen(wx.Pen(wx.Color(0,0,0)))
                dc.DrawCircle(x_c, y_c, pt.radius+2)
            else:
                dc.SetBrush(wx.Brush(wx.Color(128,128,128), wx.SOLID))
                dc.SetPen(wx.Pen(wx.Color(0,0,0)))
                dc.DrawCircle(x_c, y_c, pt.radius)


            x = x_c 
            y = y_c
            
    def DrawGrid(self, dc):
        '''
        Draw the grid lines
        '''
        
        spacing = self.r_fieldHeight/(self.m_GridLines)
        
        dc.SetPen(wx.Pen(wx.Color(218, 218, 218)))

        for i in range(self.m_GridLines):
            y = self.m_BorderUp + (i+1) * spacing
            dc.DrawLine(self.m_BorderLeft, y,
                        self.m_BorderLeft + self.r_fieldWidth, y)

    def DrawAxis(self, dc):

        dc.SetPen(wx.Pen(wx.Color(218,218,218)))
        
        # Horizontal
        dc.DrawLine(self.m_BorderLeft - 2, self.m_BorderUp, 
                    self.m_BorderLeft + self.r_fieldWidth, self.m_BorderUp)
        dc.DrawLine(self.m_BorderLeft - 2, self.r_fieldHeight + self.m_BorderUp, 
                    self.m_BorderLeft + self.r_fieldWidth, self.r_fieldHeight + self.m_BorderUp)
        # Vertical
        dc.DrawLine(self.m_BorderLeft, self.m_BorderUp, 
                    self.m_BorderLeft, self.m_BorderUp + self.r_fieldHeight);
        dc.DrawLine(self.m_BorderLeft + self.r_fieldWidth, self.m_BorderUp, 
                    self.m_BorderLeft + self.r_fieldWidth, self.m_BorderUp + self.r_fieldHeight);

        dc.SetFont(wx.Font(self.m_labelFontPt, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

        dc.DrawText('1.0', 2, self.m_labelFontPt/2 )
        dc.DrawText('0.0', 2, self.m_BorderUp + self.r_fieldHeight)
    
        for i, t in enumerate('Opacity'):
            dc.DrawText(t, 6, self.m_BorderUp + (2+i)*self.m_labelFontPt)

    
        dc.DrawText('Values', (self.m_BorderLeft + self.r_fieldWidth)/2, 
                self.m_BorderUp +  self.r_fieldHeight)

    def DrawFill(self, dc):
        ''' Draws the interpolated fill'''
        yat = self.y_from_alpha(0.0)

        for i in range(self.r_fieldWidth):
            x = self.m_BorderLeft + i
            rgba = self.rgba_from_value(self.value_from_x(x))
            dc.SetPen(wx.Pen(wx.Color(rgba[0], rgba[1], rgba[2])))
            dc.DrawLine(x, self.y_from_alpha(rgba[3]), x, yat)

    def Draw(self, dc):

        # Get the actual client size of ourselves
        width, height = self.GetClientSize()
        
        if not width or not height:
            # Nothing to do, we still don't have dimensions!
            return

        # Initialize the wx.BufferedPaintDC, assigning a background
        # colour and a foreground colour (to draw the text)
        dc.SetBackground(wx.WHITE_BRUSH)
        dc.Clear()

        # Draw the transfer function fill
        self.DrawFill(dc)
        # Draw the Grid
        self.DrawGrid(dc)
        # Draw the Axis
        self.DrawAxis(dc)
        # Draw Points
        self.DrawPoints(dc)

    def delete_current_point(self):
        """If current point is not one of the end points, remove it!
        """

        if self.cur_pt and \
                self.cur_pt not in (self.points[0], self.points[-1]):
                   idx = self.points.index(self.cur_pt) 
                   del self.points[idx]

                   self.cur_pt = None
                   self.Refresh()

    def get_current_point_info(self):
        """Return scalar value and rgba of currently selected point.

        @retuns: (scalar_value, (r,g,b), alpha)
        """

        if self.cur_pt:
            c = self.cur_pt
            return (c.value, c.color, c.alpha)

        else:
            return None

    def set_current_point_colour(self, colour):
        if self.cur_pt:
            self.cur_pt.color = colour
            # we've only changed the colour of this point, so we can
            # refresh the display (no sorting required)
            self.SendCurPointChanged()
            self.Refresh()

    def get_min_max(self):
        """Return min and max scalars of the transfer function.
        """

        return self.points[0].value, self.points[-1].value

    def set_min_max(self, min, max):
        """Update the scalar range of the transfer function. 
        """

        if not min < max:
            return

        # this will make sure all points are inside the range
        for p in self.points:
            if p.value < min:
                p.value = min
            elif p.value > max:
                p.value = max

        # take first point and last point, change their scalar values
        # to be on the extrema of the range.
        self.points[0].value = min
        self.points[-1].value = max

        self._update_size()

        self.Refresh()

    def get_transfer_function(self):
        """Returns transfer function as a sorted list of tuples, where
        each tuple is (value, (r,g,b), opacity).
        """

        tf = []
        for p in self.points:
            tf.append((p.value, p.color, p.alpha))

        return tf


    def set_transfer_function(self, transfer_function):
        """Overwrite current transfer function with transfer_function,
        a list of tuples with each tuple (value, (r,g,b), opacity).
        """

        if len(transfer_function) < 2:
            return

        self.points = []
        for pinfo in transfer_function:
            self.points.append(
                    TransferPoint(pinfo[0], pinfo[1], pinfo[2],
                        fixed=False))

        self.points.sort()

        self.points[0].fixed = True
        self.points[-1].fixed = True

        self._update_size()
        self.Refresh()

           
    def OnEraseBackground(self, event):
        ''' Called when the background is erased '''

        # It is left blank to prevent flicker
        pass

    def OnMouseDown(self, event):
        
        x = event.GetX()
        y = event.GetY()
        
        self.mouse_down = True

        for pt in self.points:
            if self.hit_test(x,y, pt):
                self.cur_pt = pt
                self.prev_x = x
                self.prev_y = y
                self.SendCurPointChanged()
                self.Refresh()
                return
        
        self.cur_pt = None

    def OnMouseDClick(self, event):
        x = event.GetX()
        y = event.GetY()

        if not self.cur_pt:
            # we can give a block of custom colour data, but we can't
            # set a default colour.  Doh!
            color_picker = wx.ColourDialog(self, self.colour_data)
        
            if color_picker.ShowModal() == wx.ID_OK:
        
                color = color_picker.GetColourData().GetColour().Get()
                self.colour_data = color_picker.GetColourData()
               
                pt = TransferPoint(
                        self.value_from_x(x), color, self.alpha_from_y(y))
                self.points.append(pt)

                self.points.sort()

                self.cur_pt = pt 
                self.SendCurPointChanged()

                self.Refresh()
           
    def OnMouseUp(self, event):
        pass
        #self.cur_pt = None

    def OnMouseMotion(self, event):
        x = event.GetX()
        y = event.GetY()

        if self.cur_pt and event.Dragging():

            self.cur_pt.alpha = self.alpha_from_y(y)

            if not self.cur_pt.fixed:
                self.cur_pt.value = self.value_from_x(x)
                self.points.sort()

            # we're dragging the current point, so it's changing
            self.SendCurPointChanged() 
            self.Refresh()

    def SendCurPointChanged(self):
        # tell handlers that the current point has changed
        event = wx.CommandEvent(EVT_CUR_PT_CHANGED_ET, self.GetId())
        event.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(event)

    def SendChangedEvent(self):

        event = wx.CommandEvent(wx.wxEVT_COMMAND_SLIDER_UPDATED, self.GetId())

        self.GetEventHandler().ProcessEvent(event)

    def _update_size(self):
        self.x, self.y = self.GetPositionTuple()
        width, height = self.GetClientSize()

        # The number of usable pixels on the graph
        self.r_fieldWidth = (width - (self.m_BorderRight + self.m_BorderLeft))
        self.r_fieldHeight = (height - (self.m_BorderUp + self.m_BorderDown))
        # The number of value data points
        self.r_rangeWidth = (self.points[-1].value -
                self.points[0].value)
        # Pixels per value
        self.pixel_per_value = float(self.r_fieldWidth) / self.r_rangeWidth


    # Manipulation functions
    def x_from_value(self, value):
        
        minv = self.points[0].value
        maxv = self.points[-1].value
        if value > maxv:
#            print 'Warning x_from_value value out of range', value
            return self.r_fieldWidth + self.m_BorderLeft
        
        if value < minv:
#            print 'Warning x_from_value value out of range', value
            return self.m_BorderLeft
        
        return self.m_BorderLeft + \
                round(self.pixel_per_value * (value-minv))
    
    def y_from_alpha(self, alpha):

        if alpha < 0: 
            return self.m_BorderUp
        if alpha > 1.0:
            return 0

        return self.m_BorderUp + int(self.r_fieldHeight*(1 - alpha))

    def value_from_x(self, xc):
        minv = self.points[0].value
        maxv = self.points[-1].value

        if xc < self.m_BorderLeft:
            return float(minv)            
        if xc >= self.r_fieldWidth + self.m_BorderLeft:
            return float(maxv)

        return float(minv) + \
                self.r_rangeWidth * \
                float(xc - self.m_BorderLeft) / self.r_fieldWidth

    def alpha_from_y(self, yc):

        if yc < self.m_BorderUp:
            return 1.0
        if yc > self.m_BorderUp + self.r_fieldHeight:
            return 0.0

        return 1.0 - float(yc - self.m_BorderUp)/self.r_fieldHeight;

    def hit_test(self, x, y, pt):
        """Does event-coordinate (x,y) fall somewhere on the point pt?
        """

        x_c = self.x_from_value(pt.value)
        y_c = self.y_from_alpha(pt.get_alpha())
        rs = pt.radius ** 2 # radius squared

        if (x - x_c) ** 2 + (y - y_c) ** 2 <= rs:
            return True

        return False
     
    def rgba_from_value(self, value):
        
        minv = self.points[0].value
        maxv = self.points[-1].value

        if not (value >= minv and value <= maxv):
            raise Exception, 'Value out of range: ' + str(value)

        for pt_i in range(len(self.points)):
            pt_cur = self.points[pt_i]
            pt_next = self.points[pt_i + 1]
            
            value_cur = pt_cur.value
            value_next = pt_next.value

            if value_cur < value:
                if value_next > value:
                    target = (value - value_cur)/float(value_next - value_cur)
                    
                    cur_color = pt_cur.get_rgba()
                    next_color = pt_next.get_rgba()
                    return self.interpolate(target, cur_color, next_color)  
                elif value_next == value:
                    return pt_next.get_rgba()
            elif value_cur == value:
                return pt_cur.get_rgba() 
            else:
                print 'Value, ', value, value_cur 
                raise Exception, 'Value is weird'

        return []
    
    def interpolate(self, target, val1, val2):
        return [target*(v2) + (1.0 - target)*v1 for v1, v2 in zip(val1, val2)]
    
    def get_map(self):
        ''' Get the interpolated values '''
        return numpy.array([self.rgba_from_value(i) for i in range(int(self.r_rangeWidth) + 1)], dtype=numpy.float32)

# You don't need anything below this
class TGraphDemo(wx.Frame):

    def __init__(self, parent, id=wx.ID_ANY, title="", pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE):

        wx.Frame.__init__(self, parent, id, title, pos, size, style)

        panel = wx.Panel(self, -1)

        # Initialize the widget
        self.t_graph = TransferFunctionWidget(panel, -1,  "Transfer Function", size=wx.Size(300, 150))

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(panel , 1)
        
        self.SetSizer(mainSizer)
        mainSizer.Layout()

        # Bind the updated event
        self.t_graph.Connect(-1, -1, wx.wxEVT_COMMAND_SLIDER_UPDATED, self.OnTGraphUpdate)

    def OnTGraphUpdate(self, event):
        # Use this to get an RGBA matrix
        # self.t_graph.get_map()
        print 'Yay new values!'

if __name__ == '__main__':
    app = wx.App()
    frame = TGraphDemo(None, -1, 'Transfer Function Graph Demo', 
                            wx.DefaultPosition, wx.Size(300,150))
    frame.Show()
    app.MainLoop()

