import string
import sys
import time
import wx
import wx.html

import resources.python.mainFrame
import resources.graphics.images

class WXInterface(wx.App):
    """Main devide application class.

    Class that's used as communication hub for most other components of the
    platform.  We've derived from wxApp but this is not a requirement... we
    could just as well have contained the wxApp instance.  This inheritance
    does not prevent abstraction from the GUI.
    """
    
    def __init__(self, devide_app):
        self._devide_app = devide_app
        
        self._mainFrame = None

        wx.App.__init__(self, 0)

        self._graphEditor = None
        self._pythonShell = None
        self._helpClass = None

    def OnInit(self):
        """Standard WX OnInit() method, called during construction.
        """

        # set the wx.GetApp() application name
        self.SetAppName('DeVIDE')
        
        self._mainFrame = resources.python.mainFrame.mainFrame(
            None, -1, "dummy", name="DeVIDE")

        wx.InitAllImageHandlers()
        self._mainFrame.SetIcon(self.getApplicationIcon())

        wx.EVT_MENU(self._mainFrame, self._mainFrame.fileExitId,
                    self.exitCallback)
        
        wx.EVT_MENU(self._mainFrame, self._mainFrame.windowGraphEditorId,
                   self._handlerMenuGraphEditor)
        wx.EVT_MENU(self._mainFrame, self._mainFrame.windowPythonShellId,
                    self._handlerMenuPythonShell)

        wx.EVT_MENU(self._mainFrame, self._mainFrame.windowMinimiseChildrenId,
                    lambda e: self._windowIconizeAllChildren())
        wx.EVT_MENU(self._mainFrame, self._mainFrame.windowRestoreChildrenId,
                    lambda e: self._windowRestoreAllChildren())
        
        wx.EVT_MENU(self._mainFrame, self._mainFrame.testingAllTestsId,
                    self._handlerTestingAllTests)
        wx.EVT_MENU(self._mainFrame, self._mainFrame.helpContentsId,
                    self._handlerHelpContents)
        wx.EVT_MENU(self._mainFrame, self._mainFrame.helpAboutId,
                    self.aboutCallback)

        self._mainFrame.Show(1)
        # here we also show twice: in wxPython 2.4.2.4 the TextCtrls sometimes
        # have difficulty completely drawing themselves at startup
        self._mainFrame.Show(1)

        # with these calls, we force an immediate draw of the full window
        # if we don't do this, some of the controls are only drawn when
        # startup progress is 100% (this is on wxPython 2.6.0.1)
        self._mainFrame.Refresh()
        self._mainFrame.Update()

        self.SetTopWindow(self._mainFrame)

        return True
        
    def OnExit(self):
        pass
    
    def getApplicationIcon(self):
        icon = wx.EmptyIcon()
        icon.CopyFromBitmap(
            resources.graphics.images.getdevidelogo32x32Bitmap())
        return icon

    def getMainWindow(self):
        return self._mainFrame        

    def get_main_window(self):
        return self.getMainWindow()

    def _handlerHelpContents(self, event):
        self.showHelp()

    def _handlerTestingAllTests(self, event):
        import testing
        reload(testing)
        dt = testing.devideTesting(self._devide_app)
        dt.runAllTests()

    def handler_post_app_init(self):
        """AFTER we've started the GUI and performed all pre-imports, this
        method makes sure that all other dependencies are imported into the
        module namespace.  We want these imports here, else the pre-imports
        can't do their thing.
        """
    
        global graphEditor, pythonShell, helpClass
    
        from graphEditor import graphEditor
        from pythonShell import pythonShell
        from helpClass import helpClass

        self.startGraphEditor()

    def quit(self):
        """Event handler for quit request.

        Calls close on the app class, which will in turn call our close()
        handler.
        """
        
        self._devide_app.close()

    def close(self):
        # take care of the graphEditor if it exists
        if self._graphEditor:
            self._graphEditor.close()
            
        # take down the help
        if self._helpClass:
            self._helpClass.close()
        
        # take care of main window
        self._mainFrame.Close()

    def showHelp(self):
        self._startHelpClass()
        self._helpClass.show()

    def startPythonShell(self):
        if self._pythonShell == None:
            self._pythonShell = pythonShell(self.getMainWindow(),
                                            'Main DeVIDE Python Introspection',
                                            self.getApplicationIcon(),
                                            self._devide_app.get_appdir())
            self._pythonShell.injectLocals({'devide_app' : self._devide_app})
            self._pythonShell.setStatusBarMessage(
                "'devide_app' is bound to the main app class.")
        else:
            self._pythonShell.show()

    def _startHelpClass(self):
        if self._helpClass == None:
            self._helpClass = helpClass(self._devide_app.get_appdir())

    def startGraphEditor(self):
        if self._graphEditor == None:
            self._graphEditor = graphEditor(self, self._devide_app)
        else:
            self._graphEditor.show()

    def log_error_list(self, msgs):
        """Log a list of strings as error.

        This method must be supplied by all interfaces.
        """

        for msg in msgs:
            wx.LogError(msg)

        wx.Log_FlushActive()

    def log_error(self, message):
        """Log a single string as error.

        This method must be supplied by all interfaces.
        """
        
        self.log_error_list([message])

    def log_info(self, message, timeStamp=True):
        """Log information.

        This will simply go into the log window.
        """
        
        if timeStamp:
            msg = "%s: %s" % (
                time.strftime("%X", time.localtime(time.time())),
                message)
        else:
            msg = message
                              
        self._mainFrame.messageLogTextCtrl.AppendText(
            msg + '\n')
        

    def log_message(self, message, timeStamp=True):
        """Use this to log a message that has to be shown to the user in
        for example a message box.
        """

        wx.LogMessage(message)
        wx.Log_FlushActive()

    def log_warning(self, message, timeStamp=True):
        wx.LogWarning(message)
        wx.Log_FlushActive()

    def set_progress(self, progress, message, noTime=False):
        self._mainFrame.progressGauge.SetValue(
            int(round(progress)))
        self._mainFrame.progressText.SetLabel(message)

        # we also output an informative message to standard out
        # in cases where DeVIDE is very busy, this is quite
        # handy.
        print "%s: %.2f" % (message, progress)

        # activate the busy cursor (we're a bit more lenient
        # on its epsilon)
        if abs(progress - 100.0) > 1:
            if not wx.IsBusy():
                wx.BeginBusyCursor()
                            
            # or switch it off
        else:
            if wx.IsBusy():
                wx.EndBusyCursor()

            # let's also show the completion message in the
            # message log...
            self.log_info(message)
                   
        # bring this window to the top if the user wants it
        if self._mainFrame.progressRaiseCheckBox.GetValue():
            self._mainFrame.Raise()

        # we want wx to update its UI, but it shouldn't accept any
        # user input, else things can get really crazy. -
        # we do keep interaction for the main window enabled,
        # but we disable all menus.
        menuCount = self._mainFrame.GetMenuBar().GetMenuCount()
        for menuPos in range(menuCount):
            self._mainFrame.GetMenuBar().EnableTop(menuPos, False)
            
        wx.SafeYield(win=self._mainFrame)

        for menuPos in range(menuCount):
            self._mainFrame.GetMenuBar().EnableTop(menuPos, True)


    def start_main_loop(self):
        self.MainLoop()

    def aboutCallback(self, event):
        from resources.python.aboutDialog import aboutDialog

        about = aboutDialog(self._mainFrame, -1, 'dummy')

        about.icon_bitmap.SetBitmap(
            resources.graphics.images.getdevidelogo64x64Bitmap())

        # set the main name and version
        about.name_version_text.SetLabel(
            'DeVIDE %s' % (self._devide_app.get_devide_version(),))

        # now get all other versions we require
        pyver = string.split(sys.version)[0]

        about.versions_listbox.Append('Python %s' % (pyver,))
        about.versions_listbox.Append('wxPython %s' % (wx.VERSION_STRING))

        # get versions of all included kits; by this time moduleManager
        # has been imported
        kits_and_versions = []
        import module_kits
        for module_kit in module_kits.module_kit_list:
            v = getattr(module_kits, module_kit).VERSION
            about.versions_listbox.Append('%s: %s' % (module_kit, v))

        about.CentreOnParent(wx.BOTH)
        about.ShowModal()
        about.Destroy()

    def exitCallback(self, event):
        self.quit()

    def _handlerMenuGraphEditor(self, event):
        self.startGraphEditor()

    def _handlerMenuPythonShell(self, event):
        self.startPythonShell()

    def showMainWindow(self):
        """Make the main window visible and bring it to the front.
        """

        self._mainFrame.Show(True)
        self._mainFrame.Raise()

    def _windowIconizeAllChildren(self):
        children = self._mainFrame.GetChildren()

        for w in children:
            try:
                if w.IsShown() and not w.IsIconized():
                    try:
                        w.Iconize()

                    except wx.PyAssertionError:
                        # we get this if it's not created yet
                        pass

            except AttributeError:
                # it's a panel for instance
                pass
            

    def _windowRestoreAllChildren(self):
        children = self._mainFrame.GetChildren()

        for w in children:
            
                try:
                    # we don't want to attempt to restore things that are
                    # hidden... only iconized
                    if w.IsShown() and w.IsIconized():
                        try:
                            w.Restore()
                            # after a restore, we have to do a show,
                            # or windows go crazy under Weendows.
                            w.Show()

                        except wx.PyAssertionError:
                            # this is usually "not implemented" on gtk, so we
                            # do an ugly work-around: store the window
                            # position, hide it, show it, reposition it -
                            # this even works under KDE
                            p = w.GetPosition() 
                            w.Hide()
                            w.Show()
                            w.SetPosition(p)
                            
                
                except AttributeError:
                    # panels and stuff simply don't have this method
                    pass
            
