import wx
from wx import py
from wx import stc

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

        self._setup_folding_and_numbers()

        self.interp = None

        # Assign handlers for keyboard events.
        self.Bind(wx.EVT_CHAR, self._handler_char)
        self.Bind(stc.EVT_STC_MARGINCLICK, self._handler_marginclick)

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

    def _handler_marginclick(self, evt):
        # fold and unfold as needed
        if evt.GetMargin() == 2:
            if evt.GetShift() and evt.GetControl():
                self._fold_all()
            else:
                lineClicked = self.LineFromPosition(evt.GetPosition())

                if self.GetFoldLevel(lineClicked) & stc.STC_FOLDLEVELHEADERFLAG:
                    if evt.GetShift():
                        self.SetFoldExpanded(lineClicked, True)
                        self._fold_expand(lineClicked, True, True, 1)
                    elif evt.GetControl():
                        if self.GetFoldExpanded(lineClicked):
                            self.SetFoldExpanded(lineClicked, False)
                            self._fold_expand(lineClicked, False, True, 0)
                        else:
                            self.SetFoldExpanded(lineClicked, True)
                            self._fold_expand(lineClicked, True, True, 100)
                    else:
                        self.ToggleFold(lineClicked)

            

    def _fold_all(self):
        lineCount = self.GetLineCount()
        expanding = True

        # find out if we are folding or unfolding
        for lineNum in range(lineCount):
            if self.GetFoldLevel(lineNum) & stc.STC_FOLDLEVELHEADERFLAG:
                expanding = not self.GetFoldExpanded(lineNum)
                break

        lineNum = 0

        while lineNum < lineCount:
            level = self.GetFoldLevel(lineNum)
            if level & stc.STC_FOLDLEVELHEADERFLAG and \
               (level & stc.STC_FOLDLEVELNUMBERMASK) == stc.STC_FOLDLEVELBASE:

                if expanding:
                    self.SetFoldExpanded(lineNum, True)
                    lineNum = self._fold_expand(lineNum, True)
                    lineNum = lineNum - 1
                else:
                    lastChild = self.GetLastChild(lineNum, -1)
                    self.SetFoldExpanded(lineNum, False)

                    if lastChild > lineNum:
                        self.HideLines(lineNum+1, lastChild)

            lineNum = lineNum + 1



    def _fold_expand(self, line, doExpand, force=False, visLevels=0, level=-1):
        lastChild = self.GetLastChild(line, level)
        line = line + 1

        while line <= lastChild:
            if force:
                if visLevels > 0:
                    self.ShowLines(line, line)
                else:
                    self.HideLines(line, line)
            else:
                if doExpand:
                    self.ShowLines(line, line)

            if level == -1:
                level = self.GetFoldLevel(line)

            if level & stc.STC_FOLDLEVELHEADERFLAG:
                if force:
                    if visLevels > 1:
                        self.SetFoldExpanded(line, True)
                    else:
                        self.SetFoldExpanded(line, False)

                    line = self._fold_expand(line, doExpand, force, visLevels-1)

                else:
                    if doExpand and self.GetFoldExpanded(line):
                        line = self._fold_expand(line, True, force, visLevels-1)
                    else:
                        line = self._fold_expand(
                            line, False, force, visLevels-1)
            else:
                line = line + 1

        return line

    def _setup_folding_and_numbers(self):
        # from our direct ancestor
        self.setDisplayLineNumbers(True)

        # the rest is from the wxPython StyledControl_2 demo
        self.SetProperty("fold", "1")

        self.SetMargins(0,0)
        self.SetEdgeMode(stc.STC_EDGE_BACKGROUND)
        self.SetEdgeColumn(78)
        self.SetMarginType(2, stc.STC_MARGIN_SYMBOL)
        self.SetMarginMask(2, stc.STC_MASK_FOLDERS)
        self.SetMarginSensitive(2, True)
        self.SetMarginWidth(2, 12)
        

        # Like a flattened tree control using circular headers and curved joins
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPEN,
                          stc.STC_MARK_CIRCLEMINUS, "white", "#404040")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDER,
                          stc.STC_MARK_CIRCLEPLUS, "white", "#404040")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERSUB,
                          stc.STC_MARK_VLINE, "white", "#404040")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERTAIL,
                          stc.STC_MARK_LCORNERCURVE, "white", "#404040")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEREND,
                          stc.STC_MARK_CIRCLEPLUSCONNECTED, "white", "#404040")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPENMID,
                          stc.STC_MARK_CIRCLEMINUSCONNECTED, "white",
                          "#404040")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERMIDTAIL,
                          stc.STC_MARK_TCORNERCURVE, "white", "#404040")
    

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
        
    
    def autoCompleteShow(self, command):
        """Display auto-completion popup list."""

        if self.interp is None:
            return
        
        list = self.interp.getAutoCompleteList(
            command, 
            includeMagic=self.autoCompleteIncludeMagic, 
            includeSingle=self.autoCompleteIncludeSingle, 
            includeDouble=self.autoCompleteIncludeDouble)
        
        if list:
            options = ' '.join(list)
            offset = 0
            self.AutoCompShow(offset, options)

        
        
