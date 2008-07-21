# Original code TransferFunctionWidget.py found at
# http://www.siafoo.net/snippet/122 on 20080721
# wxWindows Library License, copyright Stou S. <stou@icapsid.net>

# modified for integration in DeVIDE by Charl P. Botha <cpbotha.net>
#

import wx
import numpy

class TransferPoint(object):
    
    def __init__(self, value, color, alpha, fixed = False):
        self.value = value
        # Color is 0 to 255
        self.color = color
        # Alpha is 0.0 to 1.0
        self.alpha = alpha
    
        if len(color) != 3:
            raise Exception, 'Color should have length of 3'

        self.selected = False
        self.pix_size = 4
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
   
    def is_selected(self):
        return self.selected
    
    def set_selected(self, selected):
        self.selected = selected       


class TransferFunctionWidget(wx.PyControl):

    def __init__(self, parent, id=wx.ID_ANY, label="", pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.NO_BORDER, validator=wx.DefaultValidator,
                 name="TransferFunction"):
        
        wx.PyControl.__init__(self, parent, id, pos, size, style, validator, name)
        
        # Local Variables
        self.m_BorderLeft = 20
        self.m_BorderUp = 5
        self.m_BorderRight = 5
        self.m_BorderDown = 13

        self.m_GridLines = 10
        self.m_TickSize = 4
        self.m_TickBorder = 2
        self.m_labelFontPt = 10;

        # The transfer points
        self.points = []
        self.points.append(TransferPoint(0, [255, 255, 255], 0, fixed=True))
        self.points.append(TransferPoint(255, [0, 0, 0], 1.0, fixed=True))

        self.m_MinMax = (0.0, 255.0)
        
        self.mouse_down = False
        self.prev_x = 0
        self.prev_y = 0
        self.cur_pt = None

        # This is always return -1 wtf.
        self.x, self.y = self.GetPositionTuple()
        width, height = self.GetClientSize()
        
        # The number of usable pixels on the graph
        self.r_fieldWidth = (width - (self.m_BorderRight + self.m_BorderLeft))
        self.r_fieldHeight = (height - (self.m_BorderUp + self.m_BorderDown))

        # The number of value data points
        self.r_rangeWidth = (self.m_MinMax[1] - self.m_MinMax[0])
        # Pixels per value
        self.pixel_per_value = float(self.r_fieldWidth) / self.r_rangeWidth

        # Bind events
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)

        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnMouseDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnMouseUp)
        self.Bind(wx.EVT_MOTION, self.OnMouseMotion)

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

        dc.SetBrush(wx.Brush(wx.Color(255,0,0), wx.SOLID))
        
        x = self.x_from_value(self.m_MinMax[0])
        y = self.y_from_alpha(0.0)
        
        for pt in self.points:
            
            x_c = self.x_from_value(pt.value)
            y_c = self.y_from_alpha(pt.get_alpha())

            dc.SetPen(wx.Pen(wx.Color(0,0,0)))   
            dc.DrawLine(x, y, x_c, y_c)

            if pt.selected:
                dc.SetPen(wx.Pen(wx.Color(0, 0, 255), 2))
                dc.DrawRectangle(x_c - 3, y_c -3, 6, 6)

            dc.SetPen(wx.Pen(wx.Color(255,0,0)))
            dc.DrawRectangle(x_c - 2, y_c -2, 4, 4)    

            x = x_c 
            y = y_c
            
    def DrawGrid(self, dc):
        '''
        Draw the grid lines
        '''
        
        width, height = self.GetClientSize()
        x, y = self.GetPositionTuple()
        
        spacing = height/(self.m_GridLines + 1)
        
        dc.SetPen(wx.Pen(wx.Color(218, 218, 218)))

        for i in range(self.m_GridLines):
            dc.DrawLine(x + self.m_BorderLeft, y + (1 + i)*spacing, 
                        x + self.m_BorderLeft + self.r_fieldWidth, y + (1 + i)*spacing)

    def DrawAxis(self, dc):

        dc.SetPen(wx.Pen(wx.Color(218,218,218)))
        
        # Horizontal
        dc.DrawLine(self.x + self.m_BorderLeft - 2, self.y + self.m_BorderUp, 
                    self.x + self.m_BorderLeft + self.r_fieldWidth, self.y + self.m_BorderUp)
        dc.DrawLine(self.x + self.m_BorderLeft - 2, self.y + self.r_fieldHeight + self.m_BorderUp, 
                    self.x + self.m_BorderLeft + self.r_fieldWidth, self.y + self.r_fieldHeight + self.m_BorderUp)
        # Vertical
        dc.DrawLine(self.x + self.m_BorderLeft, self.y + self.m_BorderUp, 
                    self.x + self.m_BorderLeft, self.y + self.m_BorderUp + self.r_fieldHeight);
        dc.DrawLine(self.x + self.m_BorderLeft + self.r_fieldWidth, self.y + self.m_BorderUp, 
                    self.x + self.m_BorderLeft + self.r_fieldWidth, self.y + self.m_BorderUp + self.r_fieldHeight);

        dc.SetFont(wx.Font(self.m_labelFontPt, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

        dc.DrawText('1.0', self.x + 2, self.y + self.m_labelFontPt/2 )
        dc.DrawText('0.0', self.x + 2, self.y + self.m_BorderUp +  self.r_fieldHeight)
    
        for i, t in enumerate('Opacity'):
            dc.DrawText(t, self.x + 6, self.y + self.m_BorderUp + (2+i)*self.m_labelFontPt)

    
#        int strw = 0;
#        int strh = 0;
#    
#        fl_measure(m_strRangeFrom.c_str(), strw, strh);
#        fl_draw(m_strRangeFrom.c_str(), x() + m_BorderLeft - strw/2, y() + m_BorderUp + r_fieldHeight + m_labelFontPt);
#        fl_measure(m_strRangeTo.c_str(), strw, strh);
#        fl_draw(m_strRangeTo.c_str(), x() + m_BorderLeft + r_fieldWidth - strw , y() + m_BorderUp + r_fieldHeight + m_labelFontPt);

        dc.DrawText('Values', (self.m_BorderLeft + self.r_fieldWidth)/2, self.y + self.m_BorderUp +  self.r_fieldHeight)

    def DrawFill(self, dc):
        ''' Draws the interpolated fill'''
        yat = self.y_from_alpha(0.0)

        for i in range(self.r_fieldWidth):
            x = self.m_BorderLeft + self.x + i
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
                pt.selected = not pt.selected
                self.prev_x = x
                self.prev_y = y
                return
        
        self.cur_pt = None
            
    def OnMouseUp(self, event):
        x = event.GetX()
        y = event.GetY()

        if not self.cur_pt:
            
            color_picker = wx.ColourDialog(self)
        
            if color_picker.ShowModal() == wx.ID_OK:
        
                color = color_picker.GetColourData().GetColour().Get()
                
                self.points.append(TransferPoint(self.value_from_x(x), color, self.alpha_from_y(y)))
                self.points.sort()
                self.SendChangedEvent()

        self.mouse_down = False
        self.Refresh()

    def OnMouseMotion(self, event):
        x = event.GetX()
        y = event.GetY()

        if self.cur_pt and self.mouse_down:

            self.cur_pt.alpha = self.alpha_from_y(y)

            if not self.cur_pt.fixed:
                self.cur_pt.value = self.value_from_x(x)
                self.points.sort()
            
            self.SendChangedEvent()
            self.Refresh()

    def SendChangedEvent(self):

        event = wx.CommandEvent(wx.wxEVT_COMMAND_SLIDER_UPDATED, self.GetId())

        self.GetEventHandler().ProcessEvent(event)

    # Manipulation functions
    def x_from_value(self, value):
        
        if value > self.m_MinMax[1]:
#            print 'Warning x_from_value value out of range', value
            return self.r_fieldWidth + self.m_BorderLeft + self.x
        
        if value < self.m_MinMax[0]:
#            print 'Warning x_from_value value out of range', value
            return self.m_BorderLeft + self.x
        
        return self.m_BorderLeft + self.x + round(self.pixel_per_value * value)
#        return self.m_BorderLeft + self.x + int(self.r_fieldWidth*((value - self.m_MinMax[0])/self.r_rangeWidth))
    
    def y_from_alpha(self, alpha):

        if alpha < 0: 
            return self.m_BorderUp + self.y
        if alpha > 1.0:
            return self.y

        return self.m_BorderUp + self.y + int(self.r_fieldHeight*(1 - alpha))

    def value_from_x(self, xc):

        if not (xc >= self.x + self.m_BorderLeft):
            return float(self.m_MinMax[0])            
        if not (xc <= self.x + self.r_fieldWidth + self.m_BorderLeft):
            return float(self.m_MinMax[1])

        return float(self.m_MinMax[0]) + self.r_rangeWidth*float(float(xc - self.x - self.m_BorderLeft)/((self.r_fieldWidth)))

    def alpha_from_y(self, yc):

        if yc < self.y + self.m_BorderUp:
            return 1.0
        if yc > self.y + self.m_BorderUp + self.r_fieldHeight:
            return 0.0

        return 1.0 - float(yc - self.y - self.m_BorderUp)/self.r_fieldHeight;

    def hit_test(self, x, y, pt):
        x_c = self.x_from_value(pt.value)
        y_c = self.y_from_alpha(pt.get_alpha())
        sz = pt.pix_size

        if x <= x_c + sz / 2 and x >= x_c - sz \
            and y <= y_c + sz and y >= y_c - sz:
                return True

        return False
     
    def rgba_from_value(self, value):
        
        if not (value >= self.m_MinMax[0] and value <= self.m_MinMax[1]):
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

