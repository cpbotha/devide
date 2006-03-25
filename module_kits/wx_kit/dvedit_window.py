import wx
from wx import py

class DVEditWindow(py.editwindow.EditWindow):

    """DeVIDE EditWindow.

    This fixes all of the py screwups by providing a re-usable Python
    EditWindow component.  The Py components are useful, they've just been put
    together in a really unfortunate way.  Poor Orbtech.

    @author: Charl P. Botha <http://cpbotha.net/>
    """

    def __init__(self, parent, id=-1, pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 style=wx.CLIP_CHILDREN | wx.SUNKEN_BORDER):

        py.editwindow.EditWindow.__init__(self, parent, id, pos, size, style)

        self.interp = None

        # Assign handlers for keyboard events.
        self.Bind(wx.EVT_CHAR, self._handler_char)

    def _handler_char(self, event):
        """Keypress event handler.
        
        Only receives an event if OnKeyDown calls event.Skip() for the
        corresponding event."""

        key = event.KeyCode()
        
        if self.interp is None:
            event.Skip()
            return

        if key in self.interp.getAutoCompleteKeys():
            # Usually the dot (period) key activates auto completion.
            if self.AutoCompActive(): 
                self.AutoCompCancel()
                
            self.ReplaceSelection('')
            self.AddText(chr(key))
            text, pos = self.GetCurLine()
            text = text[:pos]
            if self.autoComplete: 
                self.autoCompleteShow(text)
                
        elif key == ord('('):
            # The left paren activates a call tip and cancels an
            # active auto completion.
            if self.AutoCompActive(): 
                self.AutoCompCancel()
                
            self.ReplaceSelection('')
            self.AddText('(')
            text, pos = self.GetCurLine()
            text = text[:pos]
            self.autoCallTipShow(text)
            
        else:
            # Allow the normal event handling to take place.
            event.Skip()


    def set_interp(self, interp):
        """Assign new py.Interpreter instance to this EditWindow.

        This instance will be used for autocompletion.  This is often a
        py.Shell's interp instance.
        """
        
        self.interp = interp

    def autoCallTipShow(self, command):
        """Display argument spec and docstring in a popup window."""

        if self.interp is None:
            return
        
        if self.CallTipActive():
            self.CallTipCancel()
            
        (name, argspec, tip) = self.interp.getCallTip(command)
        
#         if tip:
#             dispatcher.send(signal='Shell.calltip', sender=self,
#         calltip=tip)

        if not self.autoCallTip:
            return
        
        if argspec:
            startpos = self.GetCurrentPos()
            self.AddText(argspec + ')')
            endpos = self.GetCurrentPos()
            self.SetSelection(endpos, startpos)
            
        if tip:
            curpos = self.GetCurrentPos()
            size = len(name)
            tippos = curpos - (size + 1)
            fallback = curpos - self.GetColumn(curpos)
            # In case there isn't enough room, only go back to the
            # fallback.
            tippos = max(tippos, fallback)
            self.CallTipShow(tippos, tip)
            self.CallTipSetHighlight(0, size)
        
    
    
        
        
