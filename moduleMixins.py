# $Id: moduleMixins.py,v 1.11 2003/05/13 09:22:32 cpbotha Exp $

from external.vtkPipeline.ConfigVtkObj import ConfigVtkObj
from external.vtkPipeline.vtkPipeline import vtkPipelineBrowser
import moduleUtils

class vtkPipelineConfigModuleMixin:
    """Mixin to use for modules that want to make use of the vtkPipeline
    functionality.

    Modules that use this as mixin can make use of the vtkObjectConfigure
    and vtkPipelineConfigure methods to use ConfigVtkObj and
    vtkPipelineBrowser, respectively.  These methods will make sure that you
    use only one instance of a browser/config class per object.

    In your close() method, MAKE SURE to call the close method of this Mixin.
    """

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

        self.closePipelineConfigure()
        self.closeVtkObjectConfigure()

    def _defaultObjectChoiceCallback(self, viewFrame, renderWin,
                                    objectChoice, objectDict):
        objectName = objectChoice.GetStringSelection()
        if objectDict.has_key(objectName):
            if hasattr(objectDict[objectName], "GetClassName"):
                self.vtkObjectConfigure(viewFrame, renderWin,
                                        objectDict[objectName])
        
    def _defaultPipelineCallback(self, viewFrame, renderWin, objectDict):
        # check that all objects are VTK objects (probably not necessary)
        objects1 = objectDict.values()
        objects = tuple([object for object in objects1
                         if hasattr(object, 'GetClassName')])

        self.vtkPipelineConfigure(viewFrame, renderWin, objects)


        
            
# ----------------------------------------------------------------------------

#from wxPython.wx import wxFileDialog, wxDirDialog, wxOPEN, wxID_OK
from wxPython.wx import *

class fileOpenDialogModuleMixin:
    """Module mixin to make use of file open dialog."""
    
    def filenameBrowse(self, parent, message, wildcard, style=wxOPEN):
        """Utility method to make use of wxFileDialog.

        This function will open up exactly one dialog per 'message' and this
        dialog won't be destroyed.  This persistence makes sure that the dialog
        retains its previous settings and also that there is less overhead for
        subsequent creations.  The dialog will be a child of 'parent', so when
        parent is destroyed, this dialog will be too.
        """
        if not hasattr(self, '_fo_dlgs'):
            self._fo_dlgs = {}
        if not self._fo_dlgs.has_key(message):
            self._fo_dlgs[message] = wxFileDialog(parent,
                                                  message, "", "",
                                                  wildcard, style)
        if self._fo_dlgs[message].ShowModal() == wxID_OK:
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
            self._do_dlgs[message] = wxDirDialog(parent, message, default_path)

        if self._do_dlgs[message].ShowModal() == wxID_OK:
            return self._do_dlgs[message].GetPath()
        else:
            return None

# ----------------------------------------------------------------------------

import resources.python.filenameViewModuleMixinFrame


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

    def _createViewFrame(self, frameTitle,
                         browseMsg="Select a filename",
                         fileWildcard=
                         "VTK data (*.vtk)|*.vtk|All files (*)|*",
                         objectDict=None):

        if objectDict == None:
            objectDict = {}

        parent_window = self._moduleManager.get_module_view_parent_window()
        self._viewFrame = resources.python.filenameViewModuleMixinFrame.\
                          filenameViewModuleMixinFrame(parent_window, -1,
                                                       'dummy')

        self._viewFrame.SetTitle(frameTitle)

        # make sure that a close of that window does the right thing
        EVT_CLOSE(self._viewFrame,
                  lambda e, s=self: s._viewFrame.Show(false))


        EVT_BUTTON(self._viewFrame, self._viewFrame.browseButtonId,
                   lambda e: self.browseButtonCallback(browseMsg,
                                                       fileWildcard))

        
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

        path = self.filenameBrowse(self._viewFrame, browseMsg, fileWildcard)

        if path != None:
            self._viewFrame.filenameText.SetValue(path)
        


# ----------------------------------------------------------------------------

import resources.python.noConfigModuleMixinViewFrame

class noConfigModuleMixin(vtkPipelineConfigModuleMixin):
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
        vtkPipelineConfigModuleMixin.close(self)
        self._viewFrame.Destroy()
        del self._viewFrame

    def _createViewFrame(self, frameTitle,
                         objectDict=None):

        """This will create the self._viewFrame for this module.

        objectDict is a dictionary with VTK object descriptions as keys and
        the actual corresponding instances as values.
        """

        if objectDict == None:
            objectDict = {}

        parent_window = self._moduleManager.get_module_view_parent_window()
        self._viewFrame = resources.python.noConfigModuleMixinViewFrame.\
                          noConfigModuleMixinViewFrame(parent_window, -1,
                                                       'dummy')

        self._viewFrame.SetTitle(frameTitle)

        # make sure that a close of that window does the right thing
        EVT_CLOSE(self._viewFrame,
                  lambda e, s=self: s._viewFrame.Show(false))

        self._setupObjectAndPipelineIntrospection(
            self._viewFrame, objectDict, None,
            self._viewFrame.objectChoice, self._viewFrame.objectChoiceId,
            self._viewFrame.pipelineButtonId)

        # new style standard ECAS buttons
        moduleUtils.createECASButtons(self, self._viewFrame,
                                      self._viewFrame.viewFramePanel)

    def objectChoiceCallback(self, objectDict):
        objectName = self._viewFrame.objectChoice.GetStringSelection()
        if objectDict.has_key(objectName):
            if hasattr(objectDict[objectName], "GetClassName"):
                self.vtkObjectConfigure(self._viewFrame, None,
                                          objectDict[objectName])
        
    def pipelineCallback(self, objectDict):
        # check that all objects are VTK objects (probably not necessary)
        objects1 = objectDict.values()
        objects = tuple([object for object in objects1
                         if hasattr(object, 'GetClassName')])

        self.vtkPipelineConfigure(self._viewFrame, None, objects)

# ----------------------------------------------------------------------------
