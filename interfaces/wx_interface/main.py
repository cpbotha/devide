# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

import string
import sys
import time
import wx
import wx.html

#import resources.python.mainFrame
import resources.graphics.images
import main_frame

class WXInterface(wx.App):
    """WX-based graphical user interface for DeVIDE.

    This contains all functionality that used to be in the main devide WX
    interface.  I'm still working on the division between this class and
    the graph editor.

    For now: we keep this class as small as possible; it only handles WX-app
    central events.  The GraphEditor does everything else.

    An alternative view would be that the GraphEditor is only concerned with
    the actual network editor canvas.  As I said, I'm still working on this.

    NOTE: I'm leaning towards the latter approach.
    
    A third approach would be to factor out a third class responsible for the
    rest of the main UI.  Then we'd have: WXInterface, GraphEditor, 
    MysteryClass.
    """
    
    def __init__(self, devide_app):
        self._devide_app = devide_app
        
        self._main_frame = None

        wx.App.__init__(self, 0)

        self._graph_editor = None
        self._python_shell = None
        self._helpClass = None

    def OnInit(self):
        """Standard WX OnInit() method, called during construction.
        """

        # set the wx.GetApp() application name
        self.SetAppName('DeVIDE')
        
        #self._main_frame = resources.python.mainFrame.mainFrame(
        #    None, -1, "dummy", name="DeVIDE")

        title = 'DeVIDE v%s' % (self._devide_app.get_devide_version(),)
        self._main_frame = main_frame.MainWXFrame(None, -1, title, (-1,-1),
                                                  (640,480))
        wx.InitAllImageHandlers()
        self._main_frame.SetIcon(self.getApplicationIcon())

        wx.EVT_MENU(self._main_frame, self._main_frame.fileExitId,
                    self.exitCallback)
        
        #wx.EVT_MENU(self._main_frame, self._main_frame.windowGraphEditorId,
        #           self._handlerMenuGraphEditor)
        wx.EVT_MENU(self._main_frame, self._main_frame.window_python_shell_id,
                    self._handler_menu_python_shell)

        #wx.EVT_MENU(self._main_frame, self._main_frame.windowMinimiseChildrenId,
        #            lambda e: self._windowIconizeAllChildren())
        #wx.EVT_MENU(self._main_frame, self._main_frame.windowRestoreChildrenId,
        #            lambda e: self._windowRestoreAllChildren())
        
        #wx.EVT_MENU(self._main_frame, self._main_frame.testingAllTestsId,
        #            self._handlerTestingAllTests)
        wx.EVT_MENU(self._main_frame, self._main_frame.helpShowHelpId,
                    self._handlerHelpContents)
        wx.EVT_MENU(self._main_frame, self._main_frame.helpAboutId,
                    self.aboutCallback)

        self._main_frame.Show(1)
        # here we also show twice: in wxPython 2.4.2.4 the TextCtrls sometimes
        # have difficulty completely drawing themselves at startup
        self._main_frame.Show(1)

        # with these calls, we force an immediate draw of the full window
        # if we don't do this, some of the controls are only drawn when
        # startup progress is 100% (this is on wxPython 2.6.0.1)
        self._main_frame.Refresh()
        self._main_frame.Update()

        self.SetTopWindow(self._main_frame)

        return True
        
    def OnExit(self):
        pass
    
    def getApplicationIcon(self):
        icon = wx.EmptyIcon()
        icon.CopyFromBitmap(
            resources.graphics.images.getdevidelogo32x32Bitmap())
        return icon

    def getMainWindow(self):
        return self._main_frame        

    def get_main_window(self):
        return self.getMainWindow()

    def _handlerHelpContents(self, event):
        self.showHelp()

    def _handler_test_all(self, event):
        import testing
        reload(testing)
        dt = testing.DeVIDETesting(self._devide_app)
        dt.runAllTests()

        # after testing, we have to quit...
        self.quit()

    def handler_post_app_init(self):
        """AFTER we've started the GUI and performed all pre-imports, this
        method makes sure that all other dependencies are imported into the
        module namespace.  We want these imports here, else the pre-imports
        can't do their thing.
        """
    
        global GraphEditor, PythonShell, helpClass
    
        from graph_editor import GraphEditor

        import module_kits
        from module_kits.wx_kit.python_shell import PythonShell

        from helpClass import helpClass

        self.start_graph_editor()
        
        # setup wx-based testing if necessary
        if self._devide_app.main_config.test:
            wx.EVT_TIMER(self, 999999, self._handler_test_all)
            self.timer = wx.Timer(self, 999999)
            self.timer.Start(150, True)
            

    def quit(self):
        """Event handler for quit request.

        Calls close on the app class, which will in turn call our close()
        handler.
        """
        
        self._devide_app.close()

    def close(self):
        # python shell and all its sub-windows need to be closed as well
        if self._python_shell:
            self._python_shell.close()
        
        # take care of the graphEditor if it exists
        if self._graph_editor:
            self._graph_editor.close()
            
        # take down the help
        if self._helpClass:
            self._helpClass.close()
        
        # take care of main window
        self._main_frame.Close()

    def showHelp(self):
        self._startHelpClass()
        self._helpClass.show()

    def start_python_shell(self):
        if self._python_shell == None:
            self._python_shell = PythonShell(self.getMainWindow(),
                                            'Main DeVIDE Python Introspection',
                                            self.getApplicationIcon(),
                                            self._devide_app)
            self._python_shell.inject_locals({'devide_app' : self._devide_app,
                                              'obj' : self._python_shell})
            self._python_shell.set_statusbar_message(
                "'devide_app' is bound to the main app class, "
                "'obj' to the shell.")
        else:
            self._python_shell.show()

    def _startHelpClass(self):
        if self._helpClass == None:
            self._helpClass = helpClass(self._devide_app)

    def start_graph_editor(self):
        if self._graph_editor == None:
            self._graph_editor = GraphEditor(self, self._devide_app)
        else:
            self._graph_editor.show()

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
                              
        self._main_frame.message_log_text_ctrl.AppendText(
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
        self._main_frame.progress_gauge.SetValue(
            int(round(progress)))
        self._main_frame.progress_text.SetLabel(message)

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
        #if self._main_frame.progressRaiseCheckBox.GetValue():
        #    self._main_frame.Raise()

        # we want wx to update its UI, but it shouldn't accept any
        # user input, else things can get really crazy. -
        # we do keep interaction for the main window enabled,
        # but we disable all menus.
        menuCount = self._main_frame.GetMenuBar().GetMenuCount()
        for menuPos in range(menuCount):
            self._main_frame.GetMenuBar().EnableTop(menuPos, False)
            
        wx.SafeYield(win=self._main_frame)

        for menuPos in range(menuCount):
            self._main_frame.GetMenuBar().EnableTop(menuPos, True)


    def start_main_loop(self):
        self.MainLoop()

    def aboutCallback(self, event):
        from resources.python.aboutDialog import aboutDialog

        about = aboutDialog(self._main_frame, -1, 'dummy')

        about.icon_bitmap.SetBitmap(
            resources.graphics.images.getdevidelogo64x64Bitmap())

        # set the main name and version
        about.name_version_text.SetLabel(
            'DeVIDE %s' % (self._devide_app.get_devide_version(),))

        # now get all other versions we require
        pyver = string.split(sys.version)[0]

        about.versions_listbox.Append('Python %s' % (pyver,))

        # get versions of all included kits; by this time moduleManager
        # has been imported
        kits_and_versions = []
        import module_kits
        for module_kit in module_kits.module_kit_list:
            v = getattr(module_kits, module_kit).VERSION
            about.versions_listbox.Append('%s: %s' % (module_kit, v))


        about.GetSizer().Fit(about)
        about.Layout()

        about.CentreOnParent(wx.BOTH)
        about.ShowModal()
        about.Destroy()

    def exitCallback(self, event):
        self.quit()

    def _handlerMenuGraphEditor(self, event):
        self.start_graph_editor()

    def _handler_menu_python_shell(self, event):
        self.start_python_shell()

    def _windowIconizeAllChildren(self):
        children = self._main_frame.GetChildren()

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
        children = self._main_frame.GetChildren()

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
            
