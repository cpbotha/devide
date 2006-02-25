#!/usr/bin/env python
#
# $Id$
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
import wx
import wx.lib.colourchooser as colourchooser

class PyColourChooserDialog(wx.Dialog):

    """Colour chooser dialog that makes use of pycolourchooser and tries
    to be a drop-in replacement for the wxColourDialog on platforms where
    it sucks.
    """
    
    def __init__(self, parent, colourData=None):

        """Instantiate the ColourChooserDialog.  Optionally pass a
        wxColourData object which will be used to initialise us.
        """
            
        wx.Dialog.__init__(self, parent, -1, title='Colour',
                           pos = wx.DefaultPosition)

        # do the layout
        self._layout()

        if not colourData:
            self._colourData = wx.ColourData()
                
        else:
            self._colourData = colourData


        # the following code breaks wxPython 2.6.2.1 on Centos 4.2 with
        # redhat 9 python 2.3 RPMS downloaded from wxPython.org:
        # import wx
        # cd = wx.ColourData()
        # cd.GetCustomColour(0).Red()
        # so, we have the following workaround to prevent this.
        for i in range(16):
            # get the custom colour as tuple
            cct = self._colourData.GetCustomColour(i).Get()
            #
            cct2 = list(cct)
            for j in range(3):
                if cct2[j] < 0: cct2[j] = 255
                elif cct2[j] > 255: cct2[j] = 255
            
            self._colourData.SetCustomColour(i, wx.Colour(*cct2))

        # and finally transfer whatever colourdata we have to the chooser
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
            baseCol = wx.Colour(baseColL[0], baseColL[1], baseColL[2])
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
        
        okButton = wx.Button(self, wx.ID_OK, "OK")
        okButton.SetDefault()
        cancelButton = wx.Button(self, wx.ID_CANCEL, "Cancel")
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonSizer.Add(cancelButton, 0, wx.ALL, 5)        
        buttonSizer.Add(okButton, 0, wx.ALL, 5)

	wx.InitAllImageHandlers()
        self._pyColourChooser = colourchooser.PyColourChooser(self, -1)

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(self._pyColourChooser, 0, 0)
        mainSizer.Add(buttonSizer, 0,
                      wx.ALIGN_RIGHT|wx.ALL, 5)

        self.SetSizer(mainSizer)
        mainSizer.Fit(self)
        self.SetAutoLayout(True)        
        self.Layout()

        # if the window has a parent, this will center it on the parent
        # if not, then on the screen
        self.CenterOnScreen(wx.BOTH)

def main():

    class App(wx.App):
        def OnInit(self):
            frame = wx.Frame(None, -1, 'ColourChooserDialogTest')
            showDlgId = wx.NewId()
            wx.Button(frame, showDlgId, 'Show Dialog')
            wx.EVT_BUTTON(frame, showDlgId, self.showDialog)
            frame.Show(True)
            self.SetTopWindow(frame)

            ccd = wx.ColourData()
            ccd.SetCustomColour(0, wx.Colour(255, 0, 0))
            ccd.SetCustomColour(1, wx.Colour(127, 0, 0))
            self.dlg = PyColourChooserDialog(frame, ccd)

            return True

        def showDialog(self, evt):
            if self.dlg.ShowModal() == wx.ID_OK:
                col = self.dlg.GetColourData().GetColour()
                print col
            else:
                print "Cancel"
            
    app = App()
    app.MainLoop()
    
if __name__ == '__main__':
    main()
