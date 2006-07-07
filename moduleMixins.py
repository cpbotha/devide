# $Id$

from external.vtkPipeline.ConfigVtkObj import ConfigVtkObj
from external.vtkPipeline.vtkMethodParser import VtkMethodParser
from external.vtkPipeline.vtkPipeline import vtkPipelineBrowser
from external.filebrowsebutton import FileBrowseButton, \
     FileBrowseButtonWithHistory,DirBrowseButton
import genUtils
from moduleBase import moduleBase
import moduleUtils
import module_kits.vtk_kit.utils

import wx
import wx.lib.masked

import resources.python.filenameViewModuleMixinFrame
import re
import module_kits
from module_kits.wx_kit.python_shell import PythonShell

class introspectModuleMixin(object):
    """Mixin to use for modules that want to make use of the vtkPipeline
    functionality.

    Modules that use this as mixin can make use of the vtkObjectConfigure
    and vtkPipelineConfigure methods to use ConfigVtkObj and
    vtkPipelineBrowser, respectively.  These methods will make sure that you
    use only one instance of a browser/config class per object.

    In your close() method, MAKE SURE to call the close method of this Mixin.
    """

    def miscObjectConfigure(self, parentWindow, obj, objDescription=''):
        """This will instantiate and show a pythonShell with the object that
        is being examined.

        If it is called multiple times for the same object, it will merely
        bring the pertinent window to the top.
        """

        if not hasattr(self, '_python_shells'):
            self._python_shells = {}

        if obj not in self._python_shells:
            icon = moduleUtils.getModuleIcon()

            
            self._python_shells[obj] = PythonShell(
                parentWindow,
                'Introspecting %s' % (objDescription,),
                icon,
                self._moduleManager.getAppDir())
            
            self._python_shells[obj].inject_locals({'obj' : obj})
            self._python_shells[obj].set_statusbar_message(
                "'obj' is bound to the introspected object")

        self._python_shells[obj].show()

    def closeMiscObjectConfigure(self):
        if hasattr(self, '_python_shells'):
            for pythonShell in self._python_shells.values():
                pythonShell.close()

            self._python_shells.clear()
            

    def vtkObjectConfigure(self, parent, renwin, vtk_obj):
        """This will instantiate and show only one object config frame per
        unique vtk_obj (per module instance).

        If it is called multiple times for the same object, it will merely
        bring the pertinent window to the top (by show()ing).

        parent: parent wxWindow derivative.  It's important to pass a parent,
        else the here-created window might never be destroyed.
        renwin: render window (optionally None) which will be
        render()ed when changes are made to the vtk object which is being
        configured.
        vtk_obj: the object you want to config.
        """ 
        if not hasattr(self, '_vtk_obj_cfs'):
            self._vtk_obj_cfs = {}
        if not self._vtk_obj_cfs.has_key(vtk_obj):
            self._vtk_obj_cfs[vtk_obj] = ConfigVtkObj(parent, renwin, vtk_obj)
        self._vtk_obj_cfs[vtk_obj].show()

    def closeVtkObjectConfigure(self):
        """Explicitly close() all ConfigVtkObj's that vtk_objct_configure has
        created.

        Usually, the ConfigVtkObj windows will be children of some frame, and
        when that frame gets destroyed, they will be too.  However, when this
        is not the case, you can make use of this method.
        """
        if hasattr(self, '_vtk_obj_cfs'):
            for cvo in self._vtk_obj_cfs.values():
                cvo.close()

            self._vtk_obj_cfs.clear()

    def vtkPipelineConfigure(self, parent, renwin, objects=None):
        """This will instantiate and show only one pipeline config per
        specified renwin and objects.

        parent: parent wxWindow derivative.  It's important to pass a parent,
        else the here-created window might never be destroy()ed.
        renwin: render window (optionally None) which will be render()ed
        when changes are made AND if objects is None, will be used to determine
        the pipeline.
        objects: if you don't want the pipeline to be extracted from the
        renderwindow, you can specify a sequence of objects to be used as the
        multiple roots of a partial pipeline.

        NOTE: renwin and objects can't BOTH be None/empty.
        """
        if not hasattr(self, '_vtk_pipeline_cfs'):
            self._vtk_pipeline_cfs = {}
            
        # create a dictionary key: a tuple containing renwin + objects
        # (if objects != None)
        this_key = (renwin,)
        if objects:
            this_key = this_key + objects
            
        # see if we have this pipeline lying around or not
        # if not, create it and store
        if not self._vtk_pipeline_cfs.has_key(this_key):
            self._vtk_pipeline_cfs[this_key] = vtkPipelineBrowser(
                parent, renwin, objects)

        # yay display
        self._vtk_pipeline_cfs[this_key].show()

    def closePipelineConfigure(self):
        """Explicitly close() the pipeline browser of this module.

        This should happen automatically if a valid 'parent' was passed to
        vtk_pipeline_configure(), i.e. when the parent dies, the pipeline
        browser will die too.  However, you can use this method to take
        care of it explicitly.
        """
        if hasattr(self, '_vtk_pipeline_cfs'):
            for pipeline in self._vtk_pipeline_cfs.values():
                pipeline.close()

            self._vtk_pipeline_cfs.clear()
        
    def close(self):
        """Shut down the whole shebang.

        All created ConfigVtkObjs and vtkPipelines should be explicitly
        closed down.
        """

        self.closeMiscObjectConfigure()
        self.closePipelineConfigure()
        self.closeVtkObjectConfigure()

    def _defaultObjectChoiceCallback(self, viewFrame, renderWin,
                                     objectChoice, objectDict):
        """This callack is required for the
        createStandardObjectAndPipelineIntrospection method in moduleUtils.
        """
        objectName = objectChoice.GetStringSelection()
        if objectDict.has_key(objectName):
            if hasattr(objectDict[objectName], "GetClassName"):
                self.vtkObjectConfigure(viewFrame, renderWin,
                                        objectDict[objectName])
            elif objectDict[objectName]:
                self.miscObjectConfigure(
                    viewFrame, objectDict[objectName],
                    objectDict[objectName].__class__.__name__)
        
    def _defaultPipelineCallback(self, viewFrame, renderWin, objectDict):
        """This callack is required for the
        createStandardObjectAndPipelineIntrospection method in moduleUtils.
        """
        
        # check that all objects are VTK objects (probably not necessary)
        objects1 = objectDict.values()
        objects = tuple([object for object in objects1
                         if hasattr(object, 'GetClassName')])

        if len(objects) > 0:
            self.vtkPipelineConfigure(viewFrame, renderWin, objects)

vtkPipelineConfigModuleMixin = introspectModuleMixin
            
# ----------------------------------------------------------------------------


class fileOpenDialogModuleMixin(object):
    """Module mixin to make use of file open dialog."""
    
    def filenameBrowse(self, parent, message, wildcard, style=wx.OPEN):
        """Utility method to make use of wxFileDialog.

        This function will open up exactly one dialog per 'message' and this
        dialog won't be destroyed.  This persistence makes sure that the dialog
        retains its previous settings and also that there is less overhead for
        subsequent creations.  The dialog will be a child of 'parent', so when
        parent is destroyed, this dialog will be too.

        If style has wx.MULTIPLE, this method  will return a list of
        complete file paths.
        """
        if not hasattr(self, '_fo_dlgs'):
            self._fo_dlgs = {}
        if not self._fo_dlgs.has_key(message):
            self._fo_dlgs[message] = wx.FileDialog(parent,
                                                  message, "", "",
                                                  wildcard, style)
        if self._fo_dlgs[message].ShowModal() == wx.ID_OK:
            if style & wx.MULTIPLE:
                return self._fo_dlgs[message].GetPaths()
            else:
                return self._fo_dlgs[message].GetPath()
        else:
            return None

    def closeFilenameBrowse(self):
        """Use this method to close all created dialogs explicitly.

        This should be taken care of automatically if you've passed in a valid
        'parent'.  Use this method in cases where this was not possible.
        """
        if hasattr(self, '_fo_dlgs'):
            for key in self._fo_dlgs.keys():
                self._fo_dlgs[key].Destroy()
            self._fo_dlgs.clear()

    def dirnameBrowse(self, parent, message, default_path=""):
        """Utility method to make use of wxDirDialog.

        This function will open up exactly one dialog per 'message' and this
        dialog won't be destroyed.  This function is more or less identical
        to fn_browse().
        """
        if not hasattr(self, '_do_dlgs'):
            self._do_dlgs = {}

        if not self._do_dlgs.has_key(message):
            self._do_dlgs[message] = wx.DirDialog(parent, message, default_path)

        if self._do_dlgs[message].ShowModal() == wx.ID_OK:
            return self._do_dlgs[message].GetPath()
        else:
            return None

# ----------------------------------------------------------------------------




class filenameViewModuleMixin(fileOpenDialogModuleMixin,
                              vtkPipelineConfigModuleMixin):
    """Mixin class for those modules that only need a filename to operate.

    Please call __init__() and close() at the appropriate times from your
    module class.  Call _createViewFrame() at the end of your __init__ and
    Show(1) the resulting frame.

    As with most Mixins, remember to call the close() method of this one at
    the end of your object.
    """

    def __init__(self):
        self._viewFrame = None

    def close(self):
        vtkPipelineConfigModuleMixin.close(self)
        self._viewFrame.Destroy()
        del self._viewFrame

    def _createViewFrame(self,
                         browseMsg="Select a filename",
                         fileWildcard=
                         "VTK data (*.vtk)|*.vtk|All files (*)|*",
                         objectDict=None, fileOpen=True):

        """By default, this will be a File Open dialog.  If fileOpen is
        False, it will be a File Save dialog.
        """

        self._viewFrame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager,
            resources.python.filenameViewModuleMixinFrame.\
            filenameViewModuleMixinFrame)

        self._fileOpen = fileOpen
                                               
        wx.EVT_BUTTON(self._viewFrame, self._viewFrame.browseButtonId,
                   lambda e: self.browseButtonCallback(browseMsg,
                                                       fileWildcard))
        
        if objectDict != None:
            moduleUtils.createStandardObjectAndPipelineIntrospection(
                self,
                self._viewFrame, self._viewFrame.viewFramePanel,
                objectDict, None)

        # new style standard ECAS buttons
        moduleUtils.createECASButtons(self, self._viewFrame,
                                      self._viewFrame.viewFramePanel)

    def _getViewFrameFilename(self):
        return self._viewFrame.filenameText.GetValue()

    def _setViewFrameFilename(self, filename):
        self._viewFrame.filenameText.SetValue(filename)

    def browseButtonCallback(self, browseMsg="Select a filename",
                             fileWildcard=
                             "VTK data (*.vtk)|*.vtk|All files (*)|*"):

        if self._fileOpen == 1:
            path = self.filenameBrowse(
                self._viewFrame, browseMsg, fileWildcard)
        else:
            path = self.filenameBrowse(
                self._viewFrame, browseMsg, fileWildcard, style=wx.SAVE)

        if path != None:
            self._viewFrame.filenameText.SetValue(path)

# ----------------------------------------------------------------------------
class colourDialogMixin(object):

    def __init__(self, parent):
        ccd = wx.ColourData()
        # often-used BONE custom colour
        ccd.SetCustomColour(0,wx.Colour(255, 239, 219))
        # we want the detailed dialog under windows        
        ccd.SetChooseFull(True)
        # create the dialog
        self._colourDialog = wx.ColourDialog(parent, ccd)

    def close(self):
        # destroy the dialog
        self._colourDialog.Destroy()
        # remove all references
        del self._colourDialog

    def getColourDialogColour(self):
        self._colourDialog.Show(True)
        self._colourDialog.Raise()
        if self._colourDialog.ShowModal() == wx.ID_OK:
            colour = self._colourDialog.GetColourData().GetColour()
            return tuple([c / 255.0 for c in
                          (colour.Red(), colour.Green(), colour.Blue())])
        else:
            return None

    def setColourDialogColour(self, normalisedRGBTuple):
        """This is the default colour we'll begin with.
        """

        R,G,B = [t * 255.0 for t in normalisedRGBTuple]
        self._colourDialog.GetColourData().SetColour(wx.Colour(R, G, B))


# ----------------------------------------------------------------------------

class noConfigModuleMixin(introspectModuleMixin):
    """Mixin class for those modules that don't make use of any user-config
    views.

    Please call __init__() and close() at the appropriate times from your
    module class.  Call _createViewFrame() at the end of your __init__ and
    Show(1) the resulting frame.

    As with most Mixins, remember to call the close() method of this one at
    the end of your object.
    """

    def __init__(self):
        self._viewFrame = None

    def close(self):
        introspectModuleMixin.close(self)
        self._viewFrame.Destroy()
        del self._viewFrame

    def _createViewFrame(self, objectDict=None):

        """This will create the self._viewFrame for this module.

        objectDict is a dictionary with VTK object descriptions as keys and
        the actual corresponding instances as values.  If you specify
        objectDict as none, the introspection controls won't get added.
        """

        parent_window = self._moduleManager.get_module_view_parent_window()

        viewFrame = wx.Frame(parent_window, -1,
                            moduleUtils.createModuleViewFrameTitle(self))
        viewFrame.viewFramePanel = wx.Panel(viewFrame, -1)

        viewFramePanelSizer = wx.BoxSizer(wx.VERTICAL)
        # make sure there's a 7px border at the top
        # FIXME: changed 10, 7 to tuple for wxPython 2.6
        viewFramePanelSizer.Add((10, 7), 0, wx.EXPAND)
        viewFrame.viewFramePanel.SetAutoLayout(True)
        viewFrame.viewFramePanel.SetSizer(viewFramePanelSizer)
        
        
        viewFrameSizer = wx.BoxSizer(wx.VERTICAL)
        viewFrameSizer.Add(viewFrame.viewFramePanel, 1, wx.EXPAND, 0)
        viewFrame.SetAutoLayout(True)
        viewFrame.SetSizer(viewFrameSizer)

        if objectDict != None:
            moduleUtils.createStandardObjectAndPipelineIntrospection(
                self, viewFrame, viewFrame.viewFramePanel, objectDict, None)

        moduleUtils.createECASButtons(self, viewFrame,
                                      viewFrame.viewFramePanel)

        # make sure that a close of that window does the right thing
        wx.EVT_CLOSE(viewFrame,
                  lambda e: viewFrame.Show(False))

        # set cute icon
        viewFrame.SetIcon(moduleUtils.getModuleIcon())

        self._viewFrame = viewFrame
        return viewFrame

    _createWindow = _createViewFrame

    def view(self):
        self._viewFrame.Show(True)
        self._viewFrame.Raise()

    def configToLogic(self):
        pass

    def logicToConfig(self):
        pass

    def configToView(self):
        pass

    def viewToConfig(self):
        pass

class scriptedConfigModuleMixin(introspectModuleMixin):

    """

    configList: list of tuples, where each tuple is
    (name/label, destinationConfigVar, typeDescription, widgetType, toolTip,
     optional data)
    e.g.
    ('Initial Distance', 'initialDistance', 'base:float', 'text',
    'A tooltip for the initial distance text thingy.')

    typeDescription: basetype:subtype
     basetype: base, tuple, list (list not implemented yet)
     subtype: in the case of scalar, the actual cast, e.g. float or int
              in the case of tuple, the actual cast followed by a comma
              and the number of elements

    widgetType: text,
                tupleText - your type spec HAS to be a tuple; text boxes
                            are created in a horizontal sizer
                checkbox,
                choice - optional data is a list of choices,
                filebrowser - optional data is a dict with fileMask and
                              fileMode keys, for example:
                              {'fileMode' : wx.SAVE,
                               'fileMask' :
                        'Matlab text file (*.txt)|*.txt|All files (*.*)|*.*'})
                maskedText - optional data is the kwargs dict for
                             MaskedTextCtrl instantiation, e.g.:
                         {'mask': '\(#{3}, #{3}, #{3}\)', 'formatcodes':'F-_'}

    NOTE: this mixin assumes that your module is derived from moduleBase,
    e.g. class yourModule(scriptedConfigModuleMixin, moduleBase):
    It's important that moduleBase comes after due to the new-style method
    resolution order.
    """

    def __init__(self, configList):
        self._viewFrame = None
        self._configList = configList
        self._widgets = {}

    def close(self):
        introspectModuleMixin.close(self)
        self._viewFrame.Destroy()
        del self._viewFrame

    def _createViewFrame(self, objectDict=None):
        parentWindow = self._moduleManager.getModuleViewParentWindow()

        import resources.python.defaultModuleViewFrame
        reload(resources.python.defaultModuleViewFrame)

        dMVF = resources.python.defaultModuleViewFrame.defaultModuleViewFrame
        viewFrame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager, dMVF)

        # this viewFrame doesn't have the 7-sizer yet
        sizer7 = wx.BoxSizer(wx.HORIZONTAL)
        viewFrame.viewFramePanel.GetSizer().Add(sizer7, 1,
                                                wx.ALL|wx.EXPAND, 7)

        # now let's add the wxGridSizer
        # as many rows as there are tuples in configList, 2 columns,
        # 7 pixels vgap, 4 pixels hgap
        gridSizer = wx.FlexGridSizer(len(self._configList), 2, 7, 4)
        # maybe after we've added everything?
        gridSizer.AddGrowableCol(1)
        panel = viewFrame.viewFramePanel
        for configTuple in self._configList:
            label = wx.StaticText(panel, -1, configTuple[0])
            gridSizer.Add(label, 0, wx.ALIGN_CENTER_VERTICAL, 0)
            widget = None
            if configTuple[3] == 'text':
                widget = wx.TextCtrl(panel, -1, "")

            elif configTuple[3] == 'tupleText':
                # find out how many elements
                typeD = configTuple[2]
                castString, numString = typeD.split(':')[1].split(',')
                num = int(numString)
                textWidgets = []
                twSizer = wx.BoxSizer(wx.HORIZONTAL)

                for i in range(num):
                    textWidgets.append(wx.TextCtrl(panel, -1, ""))
                    twSizer.Add(textWidgets[-1], 0, wx.ALIGN_CENTER_VERTICAL,
                                1)
                    if i < num - 1:
                        twSizer.Add(wx.StaticText(panel, -1, ','), 0, wx.RIGHT,
                                    border=4)

                widget = None
                widgets = textWidgets
                widgetsSizer = twSizer
                    

            elif configTuple[3] == 'maskedText':
                widget = wx.lib.masked.TextCtrl(panel, -1, '',
                                        **configTuple[5])
                
            elif configTuple[3] == 'checkbox': # checkbox
                widget = wx.CheckBox(panel, -1, "")
                
            elif configTuple[3] == 'choice': # choice
                widget = wx.Choice(panel, -1)
                # in this case, configTuple[5] has to be a list of strings
                for cString in configTuple[5]:
                    widget.Append(cString)

            else: # filebrowser
                widget = FileBrowseButton(
                    panel, -1,
                    fileMask=configTuple[5]['fileMask'],
                    fileMode=configTuple[5]['fileMode'],
                    labelText=None)
                
            if widget:
                if len(configTuple[4]) > 0:
                    widget.SetToolTip(wx.ToolTip(configTuple[4]))
            
                gridSizer.Add(widget, 0, wx.EXPAND, 0)
                self._widgets[configTuple[0:5]] = widget

            elif len(widgets) > 0:
                if len(configTuple[4]) > 0:
                    for w in widgets:
                        w.SetToolTip(wx.ToolTip(configTuple[4]))
                    
                gridSizer.Add(widgetsSizer, 0, wx.EXPAND, 0)
                self._widgets[configTuple[0:5]] = widgets
                

        sizer7.Add(gridSizer, 1, wx.EXPAND, 0)
        
        if objectDict != None:
            moduleUtils.createStandardObjectAndPipelineIntrospection(
                self, viewFrame, viewFrame.viewFramePanel, objectDict, None)

        moduleUtils.createECASButtons(self, viewFrame,
                                      viewFrame.viewFramePanel)
            
        self._viewFrame = viewFrame
        return viewFrame

    # legacy
    _createWindow = _createViewFrame

    def _getWidget(self, configTupleIndex):
        """Returns widget(s) given the index of the relevant configTuple in
        the configList structure.
        """
        
        return self._widgets[self._configList[configTupleIndex][0:5]]
    

    def viewToConfig(self):
        for configTuple in self._configList:
            widget = self._widgets[configTuple[0:5]]
            typeD = configTuple[2]

            if configTuple[3] == 'choice':
                wv = widget.GetStringSelection()

                # if the user has asked for a base:int, we give her
                # the index of the choice that was made; otherwise
                # we return the string on the choice at that position
                if typeD.startswith('base:'):
                    castString = typeD.split(':')[1]
                    if castString == 'int':
                        wv = widget.GetSelection()

            elif configTuple[3] == 'tupleText':
                widgets = widget
                wv = []
                for w in widgets:
                    wv.append(w.GetValue())

                wv = ','.join(wv)
                
            else:
                wv = widget.GetValue()
            
            if typeD.startswith('base:'):
                # we're only supporting 'text' widget so far
                castString = typeD.split(':')[1]
                try:
                    val = eval('%s(wv)' % (castString,))
                except ValueError:
                    # revert to default value
                    val = eval('self._config.%s' % (configTuple[1],))
                    widget.SetValue(str(val))

            elif typeD.startswith('tuple:'):
                # e.g. tuple:float,3
                castString, numString = typeD.split(':')[1].split(',')
                val = genUtils.textToTypeTuple(
                    wv, eval('self._config.%s' % (configTuple[1],)),
                    int(numString), eval(castString))

                if configTuple[3] == 'tupleText':
                    for i in range(len(widgets)):
                        widgets[i].SetValue(str(val[i]))
                        
                else:
                    widget.SetValue(str(val))

            else:
                raise ValueError, 'Invalid typeDescription.'

            setattr(self._config, configTuple[1], val)

    def configToView(self):
        # we have to do explicit casting for floats with %f, instead of just
        # using str(), as some filters return parameters as C++ float
        # (i.e. not doubles), and then str() shows us strings that are far too
        # long
        
        for configTuple in self._configList:
            widget = self._widgets[configTuple[0:5]]
            val = getattr(self._config, configTuple[1])

            typeD = configTuple[2]

            if configTuple[3] == 'text' or configTuple[3] == 'maskedText':
                if typeD.startswith('base:'):

                    castString = typeD.split(':')[1]
                    if castString == 'float':
                        widget.SetValue('%g' % (val,))
                       
                    else:
                        widget.SetValue(str(val))

                else:
                    # so this is a tuple
                    # e.g. tuple:float,3
                    castString, numString = typeD.split(':')[1].split(',')
                    if castString == 'float':
                        num = int(numString)
                        formatString = '(%s)' % ((num - 1) * '%g, ' + '%g')
                        widget.SetValue(formatString % val)

                    else:
                        # some other tuple
                        widget.SetValue(str(val))

            elif configTuple[3] == 'tupleText':
                # for a tupleText, widget is a list
                widgets = widget
                  
                if typeD.startswith('tuple'):
                    # so this is a tuple
                    # e.g. tuple:float,3
                    castString, numString = typeD.split(':')[1].split(',')

                    num = int(numString)
                    t = tuple(val)

                    for i in range(num):
                        if castString == 'float':
                            widgets[i].SetValue('%g' % (t[i],))
                        else:
                            widgets[i].SetValue(str(t[i]))
                        
            elif configTuple[3] == 'checkbox':
                widget.SetValue(bool(val))

            elif configTuple[3] == 'filebrowser':
                widget.SetValue(str(val))

            elif configTuple[3] == 'choice': # choice

                # if a choice has a type of 'int', it works with the index
                # of the selection.  In all other cases, the actual
                # string selection is used
                
                setChoiceWithString = True
                
                if typeD.startswith('base:'):
                    castString = typeD.split(':')[1]
                    if castString == 'int':
                        setChoiceWithString = False
                
                if setChoiceWithString:
                    widget.SetStringSelection(str(val))
                else:
                    
                    print "moo: %s = %d" % (configTuple[0], val)
                    widget.SetSelection(int(val))


    def view(self):
        self._viewFrame.Show(True)
        self._viewFrame.Raise()
    
                
