#!/usr/bin/env python
#
# $Id: PyColourChooserDialog.py,v 1.2 2003/05/03 19:10:33 cpbotha Exp $
#
# This python module contains a class to construct a colour chooser dialog
# using the wxPyColourChooser which is part of wxPython since 2.4.0.something.
# This dialog should function as a drop-in replacement for the native
# wxDialog.
#
# This code is distributed under the conditions of the BSD license.
# See LICENSE.txt for details.
#
# Copyright (c) 2003 Charl P. Botha
#
# This software is distributed WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the above copyright notice for more information.
#
# Author contact information:
#   Charl P. Botha <cpbotha@ieee.org>
#   http://cpbotha.net/

import colorsys
from wxPython import wx
from wxPython.lib.colourchooser import wxPyColourChooser

class PyColourChooserDialog(wx.wxDialog):

    """Colour chooser dialog that makes use of pycolourchooser and tries
    to be a drop-in replacement for the wxColourDialog on platforms where
    it sucks.
    """
    
    def __init__(self, parent, colourData=None):

        """Instantiate the ColourChooserDialog.  Optionally pass a
        wxColourData object which will be used to initialise us.
        """
            
        wx.wxDialog.__init__(self, parent, -1, title='Colour',
                             pos = wx.wxDefaultPosition)

        # do the layout
        self._layout()

        if not colourData:
            self._colourData = wx.wxColourData()
        else:
            self._colourData = colourData
            self._colourDataToPyColourChooser()

    def GetColourData(self):
        """Return the wxColourData associated with this dialog.
        """

        # first we have to synchronise our colourData with what's happened
        # in the pycolourchooser, mmmkay?
        self._pyColourChooserToColourData()

        # and then return the bugger
        return self._colourData

    def _colourDataToPyColourChooser(self):
        """Transfer state from the internal wxColourData to the internal
        PyColourChooser."""

        # let's do the custom colours
        for colIdx in range(16):
            curCol = self._colourData.GetCustomColour(colIdx)

            # now we have to synthesise the slider "base_colour" and "slidepos"
            r,g,b = (curCol.Red() / 255.0,
                     curCol.Green() / 255.0,
                     curCol.Blue() / 255.0)
            # convert to hsv
            h,s,v = colorsys.rgb_to_hsv(r,g,b)
            # with value == 1.0 and converted back to 8 bit RGB, this is base
            baseColL = [i * 255.0 for i in colorsys.hsv_to_rgb(h,s,1.0)]
            baseCol = wx.wxColour(baseColL[0], baseColL[1], baseColL[2])
            # the Value component is of course the setting of the slider
            # unfortunately we need to grab some values from the slider
            # itself.
            smax = self._pyColourChooser.slider.GetMax()
            smin = self._pyColourChooser.slider.GetMin()
            slidepos = smin + (1.0 - v) * (smax - smin)

            self._pyColourChooser.setCustomColour(colIdx, curCol,
                                                  baseCol, slidepos)
            
        # and then the currently selected colour
        self._pyColourChooser.SetValue(self._colourData.GetColour())

    def _pyColourChooserToColourData(self):
        """Transfer state from the internal PyColourChooser to the internal
        wxColourData.
        """
        self._colourData.SetColour(self._pyColourChooser.GetValue())

        # hmmm, pycolourchooser doesn't have functions for getting
        # the custom colours yet...


    def _layout(self):
        """Layout the window with the pycolourchooser and some buttons.
        """
        
        okButton = wx.wxButton(self, wx.wxID_OK, "OK")
        okButton.SetDefault()
        cancelButton = wx.wxButton(self, wx.wxID_CANCEL, "Cancel")
        buttonSizer = wx.wxBoxSizer(wx.wxHORIZONTAL)
        buttonSizer.Add(cancelButton, 0, wx.wxALL, 5)        
        buttonSizer.Add(okButton, 0, wx.wxALL, 5)

        wx.wxInitAllImageHandlers()
        self._pyColourChooser = wxPyColourChooser(self, -1)

        mainSizer = wx.wxBoxSizer(wx.wxVERTICAL)
        mainSizer.Add(self._pyColourChooser, 0, 0)
        mainSizer.Add(buttonSizer, 0,
                      wx.wxALIGN_RIGHT|wx.wxALL, 5)

        self.SetSizer(mainSizer)
        mainSizer.Fit(self)
        self.SetAutoLayout(True)        
        self.Layout()

        # if the window has a parent, this will center it on the parent
        # if not, then on the screen
        self.CenterOnScreen(wx.wxBOTH)

def main():

    class App(wx.wxApp):
        def OnInit(self):
            frame = wx.wxFrame(None, -1, 'ColourChooserDialogTest')
            showDlgId = wx.wxNewId()
            wx.wxButton(frame, showDlgId, 'Show Dialog')
            wx.EVT_BUTTON(frame, showDlgId, self.showDialog)
            frame.Show(True)
            self.SetTopWindow(frame)

            ccd = wx.wxColourData()
            ccd.SetCustomColour(0, wx.wxColour(255, 0, 0))
            ccd.SetCustomColour(1, wx.wxColour(127, 0, 0))            
            self.dlg = PyColourChooserDialog(frame, ccd)

            return True

        def showDialog(self, evt):
            if self.dlg.ShowModal() == wx.wxID_OK:
                col = self.dlg.GetColourData().GetColour()
                print col
            else:
                print "Cancel"
            
    app = App()
    app.MainLoop()
    
if __name__ == '__main__':
    main()
