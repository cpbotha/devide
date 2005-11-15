#!/usr/bin/env python
# $Id: devide.py,v 1.109 2005/11/15 09:03:27 cpbotha Exp $

# the current main release version
DEVIDE_VERSION = '20051114-T'

# standard Python imports
import getopt
import mutex
import os
import re
import stat
import string
import sys
import time
import traceback

# WX imports
# this HAS to go before we call import wx
#import fixWxImports
import wx
import wx.html

# UI imports
import resources.python.mainFrame
import resources.graphics.images

############################################################################
class mainConfigClass(object):

    def __init__(self):
        import defaults
        self.useInsight = defaults.USE_INSIGHT
        self.itkPreImport = True
        self.stereo = False
        
        self._parseCommandLine()

    def dispUsage(self):
        print "-h or --help               : Display this message."
        print "--insight or --itk         : Use ITK-based modules."
        print "--no-insight or --no-itk   : Do not use ITK-based modules."
        print "--no-itk-preimport         : Do not pre-import ITK."
        print "--stereo                   : Allocate stereo visuals."

    def _parseCommandLine(self):
        try:
            # 'p:' means -p with something after
            optlist, args = getopt.getopt(
                sys.argv[1:], 'h',
                ['help', 'no-itk', 'no-insight', 'itk', 'insight',
                 'no-itk-preimport', 'stereo'])
        except getopt.GetoptError,e:
            self.dispUsage()
            sys.exit(1)

        for o, a in optlist:
            if o in ('-h', '--help'):
                self.dispUsage()
                sys.exit(1)

            elif o in ('--insight', '--itk'):
                self.useInsight = True

            elif o in ('--no-itk', '--no-insight'):
                self.useInsight = False

            elif o in ('--no-itk-preimport',):
                self.itkPreImport = False

            elif o in ('--stereo',):
                self.stereo = True

############################################################################
class devide_app_t(wx.App):
    """Main devide application class.

    Class that's used as communication hub for most other components of the
    platform.  We've derived from wxApp but this is not a requirement... we
    could just as well have contained the wxApp instance.  This inheritance
    does not prevent abstraction from the GUI.
    """
    
    def __init__(self):
        self.mainConfig = mainConfigClass()
        
        self._inProgress = mutex.mutex()
        self._previousProgressTime = 0
        self._currentProgress = -1
        self._currentProgressMsg = ''
        
        self._mainFrame = None

        #self._appdir, exe = os.path.split(sys.executable)
        if hasattr(sys, 'frozen') and sys.frozen:
            self._appdir, exe = os.path.split(sys.executable)
        else:
            dirname = os.path.dirname(sys.argv[0])
            if dirname and dirname != os.curdir:
                self._appdir = dirname
            else:
                self._appdir = os.getcwd()
        
        wx.App.__init__(self, 0)

        self._graphEditor = None
        self._pythonShell = None
        self._helpClass = None
    

    def OnInit(self):
        """Standard WX OnInit() method, called during construction.
        """
        
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

        # load up the moduleManager; we do that here as the moduleManager
        # needs to give feedback via the GUI (when it's available)
        print "about to import moduleManager"
        global moduleManager
        import moduleManager
        self.moduleManager = moduleManager.moduleManager(self)

        # perform post initialisation and pre-loading imports
        postWxInitImports()

        # initialise the scheduler
        self.scheduler = scheduler(self)

        # indicate that we're ready to go!
        self.setProgress(100, 'Started up')

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

    def getModuleManager(self):
        return self.moduleManager

    def getAppDir(self):
        return self._appdir

    def get_appdir(self):
        return self.getAppDir()

    def _handlerHelpContents(self, event):
        self.showHelp()

    def _handlerTestingAllTests(self, event):
        import testing
        reload(testing)
        dt = testing.devideTesting(self)
        dt.runAllTests()


    def quit(self):
        # take care of the graphEditor if it exists
        if self._graphEditor:
            self._graphEditor.close()
            
        # shutdown all modules gracefully
        self.moduleManager.close()

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
                                            self.getAppDir())
            self._pythonShell.injectLocals({'devideApp' : self})
            self._pythonShell.setStatusBarMessage(
                "'devideApp' is bound to the main app class.")
        else:
            self._pythonShell.show()

    def _startHelpClass(self):
        if self._helpClass == None:
            self._helpClass = helpClass(self)

    def startGraphEditor(self):
        if self._graphEditor == None:
            self._graphEditor = graphEditor(self)
        else:
            self._graphEditor.show()

    def logError(self, msgs):
        """This method can be called by any DeVIDE component for error
        reporting.

        DeVIDE will decide how the error should be reported depending on the
        context.  For now we only have the GUI context.
        """

        for msg in msgs:
            wx.LogError(msg)

        wx.Log_FlushActive()

    def logMessage(self, message, timeStamp=True):
        if timeStamp:
            msg = "%s: %s" % (
                time.strftime("%X", time.localtime(time.time())),
                message)
        else:
            msg = message
                              
        self._mainFrame.messageLogTextCtrl.AppendText(
            msg + '\n')

    def setProgress(self, progress, message, noTime=False):
        # 1. we shouldn't call setProgress whilst busy with setProgress
        # 2. only do something if the message or the progress has changed
        # 3. we only perform an update if a second or more has passed
        #    since the previous update, unless this is the final
        #    (i.e. 100% update) or noTime is True

        # the testandset() method of mutex.mutex is atomic... this will grab
        # the lock and set it if it isn't locked alread and then return true.
        # returns false otherwise
        if self._inProgress.testandset():
            if message != self._currentProgressMsg or \
                   progress != self._currentProgress:
                if abs(progress - 100.0) < 0.01 or noTime or \
                       time.time() - self._previousProgressTime >= 1:
                    self._previousProgressTime = time.time()
                    self._currentProgressMsg = message
                    self._currentProgress = progress
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
                        self.logMessage(message)
                   
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

            # unset the mutex thingy
            self._inProgress.unlock()

    def aboutCallback(self, event):
        from resources.python.aboutDialog import aboutDialog

        aboutText1 = '''
        <html>
        <body>
        <center>
        <h3>DeVIDE v.%s</h3>
        <p>DeVIDE is copyright (c) 2003-2005 Charl P. Botha<br>
        http://cpbotha.net/DeVIDE
        </p>
        <p>Unauthorised use or distribution strictly prohibited.
        See LICENSE.txt in the docs directory for detailed terms of
        use.
        </p>
        <p>
        wxPython %s, Python %s<br>
        '''

        aboutText2 = '''
        </p>
        </center>
        </body>
        </html>
        '''

        about = aboutDialog(self._mainFrame, -1, 'dummy')
        pyver = string.split(sys.version)[0]

        # get versions of all included kits; by this time moduleManager
        # has been imported
        kits_and_versions = []
        import moduleKits
        for moduleKit in moduleKits.moduleKitList:
            v = getattr(moduleKits, moduleKit).VERSION
            kits_and_versions.append('%s: %s' % (moduleKit, v))

        # if applicable, let's make an ITK version string
#         ivs = ''
#         if self.mainConfig.useInsight:
#             # let's hope McMillan doesn't catch this one!
#             itk = __import__('fixitk')
#             isv = itk.itkVersion.GetITKSourceVersion()
#             ind = re.match('.*Date: ([0-9]+/[0-9]+/[0-9]+).*', isv).group(1)
#             ivs = '%s (%s: %s)' % (itk.itkVersion.GetITKVersion(), ind,
#                                    ITK_VERSION_EXTRA)
#         else:
#             ivs = 'N/A'



        aboutText = '%s%s%s' % (aboutText1,
                                '<br>'.join(kits_and_versions),
                                aboutText2)
        
        about.htmlWindow.SetPage(aboutText % (DEVIDE_VERSION,
                                              wx.VERSION_STRING,
                                              pyver))

        ir = about.htmlWindow.GetInternalRepresentation()
        ir.SetIndent(0, wx.html.HTML_INDENT_ALL)
        newSize = (int(1.25 * ir.GetWidth()), int(1.025 * ir.GetHeight()))
        about.SetSize(newSize)

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
            

    
# ---------------------------------------------------------------------------

def postWxInitImports():
    """AFTER we've started the GUI and performed all pre-imports, this method
    makes sure that all other dependencies are imported into the module
    namespace.  We want these imports here, else the pre-imports can't do
    their thing.
    """
    
    global graphEditor, moduleManager, scheduler, pythonShell, helpClass
    
    from graphEditor import graphEditor
    from moduleManager import moduleManager
    from scheduler import scheduler
    from pythonShell import pythonShell
    from helpClass import helpClass

def main():
    devide_app = devide_app_t()
    devide_app.startGraphEditor()
    devide_app.MainLoop()
    

if __name__ == '__main__':
    main()
    
