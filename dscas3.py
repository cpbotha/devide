#!/usr/bin/env python
# $Id: dscas3.py,v 1.66 2003/12/15 09:48:49 cpbotha Exp $

DSCAS3_VERSION = '20031214 no-ITK'

import getopt
import mutex
import os
import re
import stat
import string
import sys
import time

import startupImports
startupImports.doImports()

from assistants import assistants
from graphEditor import graphEditor
from moduleManager import moduleManager
from pythonShell import pythonShell

import resources.python.mainFrame
import resources.graphics.images

import wx
import wx.html

import vtk
import vtkdscas


class mainConfigClass(object):

    def __init__(self, argv):
        parseCommandLine()

        self.useInsight = True

    def dispUsage(self):
        print "-h or --help               : Display this message."
        print "--no-insight or --no-itk   : Do not use ITK-based modules."

    def _parseCommandLine(self):
        try:
            # 'p:' means -p with something after
            optlist, args = getopt.getopt(
                argv[1:], 'h',
                ['help', 'no-itk', 'no-insight'])
        except getopt.GetoptError,e:
            self.dispUsage()
            sys.exit(1)

        for a, o in optlist:
            if o in ('-h', '--help'):
                self.dispUsage()

            elif o in ('--no-itk', '--no-insight'):
                self.useInsight = False
        

# ---------------------------------------------------------------------------
class dscas3_app_t(wx.App):
    """Main dscas3 application class.

    Class that's used as communication hub for most other components of the
    platform.  We've derived from wxApp but this is not a requirement... we
    could just as well have contained the wxApp instance.  This inheritance
    does not prevent abstraction from the GUI.
    """
    
    def __init__(self):
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

        self._assistants = assistants(self)
        self._graphEditor = None
        self._pythonShell = None
	

    def OnInit(self):
        self._mainFrame = resources.python.mainFrame.mainFrame(None, -1,
                                                               "dummy")

        wx.InitAllImageHandlers()
        self._mainFrame.SetIcon(self.getApplicationIcon())

        wx.EVT_MENU(self._mainFrame, self._mainFrame.fileExitId,
                    self.exitCallback)
        wx.EVT_MENU(self._mainFrame, self._mainFrame.windowGraphEditorId,
                   self.graphEditorCallback)
        wx.EVT_MENU(self._mainFrame, self._mainFrame.windowPythonShellId,
                    self.pythonShellCallback)
        wx.EVT_MENU(self._mainFrame, self._mainFrame.helpAboutId,
                    self.aboutCallback)

        self._mainFrame.Show(1)
        self.SetTopWindow(self._mainFrame)
        
        # find all modules that we can use
	self.moduleManager = moduleManager(self)

        self.setProgress(100, 'Started up')

        # perform vtk initialisation
        self._vtkInit()

        return True
        

    def _vtkInit(self):
        """All VTK specific initialisation is done from here.
        """
        
        # CRITICAL VTK CUSTOMISATION BIT:
        # multi-threaded vtk objects will call back into python causing
        # re-entrancy; usually, the number of threads is set to the number
        # of CPUs, so on single-cpu machines this is no problem
        # On Linux SMP this somehow does not cause any problems either.
        # On Windows SMP the doubleThreshold module can reliably crash your
        # machine.  Give me a Windows SMP machine, and I shall fix it.
        # for now we will just make sure that threading doesn't use more
        # than one thread. :)
        vtk.vtkMultiThreader.SetGlobalMaximumNumberOfThreads(1)
        vtk.vtkMultiThreader.SetGlobalDefaultNumberOfThreads(1)
        
        # now make sure that VTK will always send error to vtk.log logfile
        temp = vtkdscas.vtkEventOutputWindow()
        temp.SetInstance(temp)

        def observerEOW(theObject, eventType):
            # theObject is of course a vtkEventOutputWindow
            textType = theObject.GetTextType()
            text = theObject.GetText()

            #print "EOW: %d - %s" % (textType, text)
            
            if textType == 0:
                # Text
                wx.LogMessage(text)
                
            elif textType == 1:
                # ErrorText
                wx.LogError(text)
                
            elif textType == 2:
                # WarningText
                wx.LogWarning(text)
                
            elif textType == 3:
                # GenericWarningText
                wx.LogWarning(text)
                
            else:
                # DebugText
                wx.LogDebug(text)

        temp.AddObserver('ErrorEvent', observerEOW)
        temp.AddObserver('WarningEvent', observerEOW)        
            
        del temp

    def OnExit(self):
        pass
    
    def getApplicationIcon(self):
        icon = wx.EmptyIcon()
        icon.CopyFromBitmap(
            resources.graphics.images.getdscas3logo32x32Bitmap())
        return icon

    def get_main_window(self):
        return self._mainFrame

    def getModuleManager(self):
	return self.moduleManager

    def get_assistants(self):
        return self._assistants

    def get_appdir(self):
        return self._appdir

    def quit(self):
        # take care of the graphEditor if it exists
        if self._graphEditor:
            self._graphEditor.close()
            
        # shutdown all modules gracefully
        self.moduleManager.close()
        
	# take care of main window
	self._mainFrame.Close()

    def startPythonShell(self):
        if self._pythonShell == None:
            self._pythonShell = pythonShell(self)
        else:
            self._pythonShell.show()

    def start_graph_editor(self):
        if self._graphEditor == None:
            self._graphEditor = graphEditor(self)
        else:
            self._graphEditor.show()

    def setProgress(self, progress, message):
        # 1. we shouldn't call setProgress whilst busy with setProgress
        # 2. only do something if the message or the progress has changed
        # 3. we only perform an update if a second or more has passed
        #    since the previous update, unless this is the final
        #    (i.e. 100% update)

        # the testandset() method of mutex.mutex is atomic... this will grab
        # the lock and set it if it isn't locked alread and then return true.
        # returns false otherwise
        if self._inProgress.testandset():
            if message != self._currentProgressMsg or \
                   progress != self._currentProgress:
                if progress >= 100 or \
                       time.time() - self._previousProgressTime >= 1:
                    self._previousProgressTime = time.time()
                    self._currentProgressMsg = message
                    self._currentProgress = progress
                    self._mainFrame.progressGauge.SetValue(progress)
                    self._mainFrame.progressText.SetLabel(message)

                    # activate the busy cursor
                    if progress < 100.0:
                        if not wx.IsBusy():
                            wx.BeginBusyCursor()
                            
                    # or switch it off
                    else:
                        if wx.IsBusy():
                            wx.EndBusyCursor()
                   
                    # bring this window to the top if the user wants it
                    if self._mainFrame.progressRaiseCheckBox.GetValue():
                        self._mainFrame.Raise()

                    # we want wx to update its UI, but it shouldn't accept any
                    # user input, else things can get really crazy.
                    wx.SafeYield()

            # unset the mutex thingy
            self._inProgress.unlock()

    def aboutCallback(self, event):
        from resources.python.aboutDialog import aboutDialog

        aboutText = '''
        <html>
        <body>
        <center>
        <h3>DSCAS3 v.%s</h3>
        <p>DSCAS3 is copyright (c) 2003 Charl P. Botha<br>
        http://cpbotha.net/phd/
        </p>
        <p>Unauthorised use or distribution strictly prohibited.
        See LICENSE.txt in the docs directory for detailed terms of
        use.
        </p>
        <p>
        wxPython %s, Python %s<br>
        VTK %s
        </p>
        </center>
        </body>
        </html>
        '''

        about = aboutDialog(self._mainFrame, -1, 'dummy')
        pyver = string.split(sys.version)[0]

        # make VTK "official version" + date of nightly (so we know
        # what to checkout)
        vsv = vtk.vtkVersion.GetVTKSourceVersion()
        # VTK source nightly date
        vnd = re.match('.*Date: ([0-9]+/[0-9]+/[0-9]+).*', vsv).group(1)
        vvs = '%s (%s)' % (vtk.vtkVersion.GetVTKVersion(), vnd)
        
        about.htmlWindow.SetPage(aboutText % (DSCAS3_VERSION,
                                              wx.VERSION_STRING,
                                              pyver,
                                              vvs))

        ir = about.htmlWindow.GetInternalRepresentation()
        ir.SetIndent(0, wx.html.HTML_INDENT_ALL)
        about.htmlWindow.SetSize((ir.GetWidth(), ir.GetHeight()))

        about.GetSizer().Fit(about)
        about.GetSizer().SetSizeHints(about)
        about.Layout()

        about.CentreOnParent(wx.BOTH)
        about.ShowModal()
        about.Destroy()

    def exitCallback(self, event):
        self.quit()

    def graphEditorCallback(self, event):
        self.start_graph_editor()

    def pythonShellCallback(self, event):
        self.startPythonShell()

	
# ---------------------------------------------------------------------------


def main():
    dscas3_app = dscas3_app_t()
    dscas3_app.MainLoop()

if __name__ == '__main__':
    main()
    
